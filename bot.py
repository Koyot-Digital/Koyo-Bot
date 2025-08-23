import os
import logging
import json
from logging import ERROR

import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()
from utils import roblox, cache
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

app = Flask(__name__)

logger = logging.getLogger("updater")
logger.setLevel(logging.INFO)

PUBLIC_KEY = os.getenv("PUBLIC_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
APP_ID = os.getenv("APP_ID")

bot_headers={
    "Authorization":"Bot "+DISCORD_TOKEN
}
with open("data/roles.json") as f:
    ROLES_CONFIG = json.load(f)


# --- Helpers ---
def verify_signature(public_key_hex, signature_hex, timestamp, body):
    verify_key = VerifyKey(bytes.fromhex(public_key_hex))
    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature_hex))
        return True
    except BadSignatureError:
        return False
def get_highest_role(category, points, roles_config):
    #Get the highest eligible role for a given category and points.
    eligible = [r for r in roles_config[category] if points >= r["points"]]
    if not eligible:
        return None
    return max(eligible, key=lambda r: r["points"])["role_id"]

def discord_api(path, method="GET", **kwargs):
    url = f"https://discord.com/api/v10{path}"
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
    return requests.request(method, url, headers=headers, **kwargs)


# --- Flask route ---
@app.route("/update", methods=["POST"])
def update_roles():
    signature = request.headers.get("X-Signature-Ed25519")
    timestamp = request.headers.get("X-Signature-Timestamp")
    body = request.data.decode("utf-8")

    if not signature:
        logger.warning("Missing signature header on Discord interaction")
        return jsonify(message='Invalid request signature'), 401

    if not verify_signature(PUBLIC_KEY, signature, timestamp, body):
        logger.warning("Invalid Discord request signature")
        return jsonify(message='Invalid request signature'), 401

    interaction = request.json


    if interaction.get("type") == 1: # Ping
        logger.info("Received Discord PING request")
        return jsonify({"type": 1}),200

    elif interaction.get("type") == 2:  # Application command
        logger.info(f"Received Discord command interaction: {interaction.get('data')}")
        id = request.json.get("id")
        token = request.json.get("token")
        callbackUrl = f"https://discord.com/api/v10/interactions/{id}/{token}/callback"
        editUrl = f"https://discord.com/api/v10/webhooks/{APP_ID}/{token}/messages/@original"
        member = interaction.get("member")
        userid = member.get("user").get("id")
        if request.json.get('data').get('id') == "1408007686884429907":

            logger.info(f"[COMMAND] /updateroles requested by {member} ({userid})")

            # Send initial response embed
            callback = requests.post(callbackUrl,json={
                "type":4,
                "data":{
                    "content": None,
                    "flags": 64,
                    "embeds": [{
                        "title":"Updating Roles",
                        "description": f"Fetching Roblox data for <@{userid}>...",
                        "color": 0x7289DA,
                        "footer": {
                            "text": "This may take a few seconds."
                        }
                    }]
                }
            }
            )
            try:
                callback.raise_for_status()
            except:
                logger.warning("request callback failed "+callback.text)

            # --- STEP 1: Roblox ID lookup ---
            roblox_id = None
            if os.getenv("USE_CACHE", "false").lower() == "true":
                roblox_id =  cache.get_cached_roblox_id(userid)
                if roblox_id:
                    logger.debug(f"[CACHE HIT] {userid} → Roblox {roblox_id}")

            if not roblox_id:
                logger.debug(f"[CACHE MISS] Fetching Roblox ID for {userid} from Bloxlink")
                roblox_id =  roblox.get_roblox_id(userid)
                if not roblox_id:
                    logger.warning(f"[NO ACCOUNT] {member} has no linked Roblox account")
                    callback = requests.patch(editUrl, json={
                        "type": 4,
                        "data": {
                            "content": None,
                            "flags": 64,
                            "embeds": [{
                                "title": "Update Failed",
                                "description": "Could not find a linked Roblox account.",
                                "color": 0xFF0000
                            }]
                        }
                    }
                    )
                    try:
                        callback.raise_for_status()
                    except:
                        logger.warning("request callback failed " + callback.text)
                    return

                if os.getenv("USE_CACHE", "false").lower() == "true":
                    cache.set_cached_roblox_id(userid, roblox_id)
                    logger.debug(f"[CACHE SET] Saved Roblox ID {roblox_id} for {userid}")

            # --- STEP 2: Fetch points ---
            points =  roblox.get_points(roblox_id)
            siteop_points = points.get("SiteopPoints", 0)
            security_points = points.get("SecurityPoints", 0)
            logger.debug(f"[POINTS] Roblox {roblox_id}: siteop={siteop_points}, security={security_points}")

            # --- STEP 3: Determine highest roles ---
            with open("data/roles.json") as f:
                roles_config = json.load(f)
            siteop_role = get_highest_role("siteop", siteop_points, roles_config)
            security_role = get_highest_role("security", security_points, roles_config)
            logger.debug(f"[ROLES ELIGIBLE] siteop={siteop_role}, security={security_role}")

            # Decide what to add/remove
            roles_to_keep, roles_to_add, roles_to_remove = [], [], []

            member_roles = member.get("roles")

            if siteop_role:
                if str(siteop_role) not in [r for r in member_roles]:
                    roles_to_add.append(siteop_role)
                roles_to_keep.append(str(siteop_role))

            if security_role:
                if str(security_role) not in [r for r in member_roles]:
                    roles_to_add.append(security_role)
                roles_to_keep.append(str(security_role))

            for category in roles_config:
                for role_cfg in roles_config[category]:
                    r_id = str(role_cfg["role_id"])
                    if r_id not in roles_to_keep and r_id in [r for r in member_roles]:
                        roles_to_remove.append(r_id)

            logger.debug(f"[ROLES CHANGE] Add={roles_to_add}, Remove={roles_to_remove}")

            # --- STEP 4: Apply changes ---
            added, removed = [], []

            base_role_url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{userid}/roles/"
            for r_id in roles_to_add:
                if r_id:
                    role_request = requests.put(base_role_url+str(r_id),headers=bot_headers)
                    try:
                        role_request.raise_for_status()
                    except:
                        logger.warning(f"role adder for role {r_id} failed: {role_request.text}")
                    added.append(r_id)
                    logger.info(f"[ROLE ADD] Added {r_id} to {userid}")

            for r_id in roles_to_remove:
                if r_id:
                    role_request = requests.delete(base_role_url + str(r_id),headers=bot_headers)
                    try:
                        role_request.raise_for_status()
                    except:
                        logger.warning(f"role remover for role {r_id} failed: {role_request.text}")
                    removed.append(r_id)
                    logger.info(f"[ROLE ADD] Added {r_id} to {userid}")

            # --- STEP 5: Send final embed ---
            added_mentions = [f"<@&{rid}>" for rid in added]
            removed_mentions = [f"<@&{rid}>" for rid in removed]
            message_embed = {
                    "content": None,
                    "flags": 64,
                    "embeds": [{
                        "title": "Roles Updated",
                        "color": 0x2ecc70,
                        "fields":[
                            {
                                "name":"👷 Site Operator",
                                "value":f"`{siteop_points}` → {f'<@&{siteop_role}>' if siteop_role else 'None'}",
                                "inline":False
                            },
                            {
                                "name": "🛡 Security",
                                "value": f"`{security_points}` → {f'<@&{security_role}>' if security_role else 'None'}",
                                "inline": False
                            },
                            {
                                "name": "📥 Added",
                                "value": ", ".join(added_mentions) if added_mentions else "None",
                                "inline": True
                            },
                            {
                                "name": "📤 Removed",
                                "value": ", ".join(removed_mentions) if removed_mentions else "None",
                                "inline": True
                            }
                        ],
                        "footer":{
                            "text" : f"Requested by {member.get("user").get("username")}"
                        }
                    }]
            }
            callback = requests.patch(editUrl, json=message_embed)
            try:
                callback.raise_for_status()
            except:
                logger.warning("request callback failed " + callback.text)
    logger.warning("Unknown interaction type received")
    return jsonify({"error": "Invalid request"}), 400

app.run(port=3000,host="0.0.0.0")
