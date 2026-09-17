import sqlite3
import time


class Database:
    def __init__(self, db_file="casino.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance REAL DEFAULT 0.0,
                stars_balance REAL DEFAULT 0.0,
                bonus_balance REAL DEFAULT 0.0,
                bet REAL DEFAULT 0.5,
                bet_currency TEXT DEFAULT 'usd',
                total_wagered REAL DEFAULT 0.0,
                total_won REAL DEFAULT 0.0,
                total_lost REAL DEFAULT 0.0,
                total_deposited REAL DEFAULT 0.0,
                total_withdrawn REAL DEFAULT 0.0,
                games_played INTEGER DEFAULT 0,
                days_registered INTEGER DEFAULT 1,
                invited_count INTEGER DEFAULT 0,
                earned_ref REAL DEFAULT 0.0,
                referrer_id INTEGER,
                is_banned INTEGER DEFAULT 0,
                is_private INTEGER DEFAULT 0,
                last_bonus INTEGER DEFAULT 0,
                created_at INTEGER DEFAULT 0
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, game_type TEXT, bet REAL, win REAL,
                multiplier REAL, result TEXT, created_at INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, type TEXT, method TEXT, amount REAL,
                commission REAL DEFAULT 0.0, status TEXT,
                external_id TEXT, created_at INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, amount REAL, check_url TEXT,
                is_activated INTEGER DEFAULT 0, created_at INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY, amount REAL,
                uses_left INTEGER, created_at INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS promo_uses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, code TEXT, created_at INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_games (
                user_id INTEGER PRIMARY KEY, game_type TEXT, state TEXT,
                bet REAL, multiplier REAL, data TEXT, created_at INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS treasury (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                crypto_manual REAL DEFAULT 0.0,
                xrocket_manual REAL DEFAULT 0.0,
                updated_at INTEGER DEFAULT 0
            )
        """)
        self.cursor.execute(
            "INSERT OR IGNORE INTO treasury (id, crypto_manual, xrocket_manual) "
            "VALUES (1, 0.0, 0.0)"
        )
        self.conn.commit()

        migrations = [
            ("username", "TEXT"), ("stars_balance", "REAL DEFAULT 0.0"),
            ("bonus_balance", "REAL DEFAULT 0.0"), ("bet", "REAL DEFAULT 0.5"),
            ("bet_currency", "TEXT DEFAULT 'usd'"), ("total_won", "REAL DEFAULT 0.0"),
            ("total_lost", "REAL DEFAULT 0.0"), ("total_deposited", "REAL DEFAULT 0.0"),
            ("total_withdrawn", "REAL DEFAULT 0.0"), ("games_played", "INTEGER DEFAULT 0"),
            ("referrer_id", "INTEGER"), ("is_banned", "INTEGER DEFAULT 0"),
            ("is_private", "INTEGER DEFAULT 0"), ("last_bonus", "INTEGER DEFAULT 0"),
            ("created_at", "INTEGER DEFAULT 0"),
        ]
        for c, t in migrations:
            self._add_column_if_not_exists(c, t)

    def _add_column_if_not_exists(self, name, typ):
        self.cursor.execute("PRAGMA table_info(users)")
        cols = [i[1] for i in self.cursor.fetchall()]
        if name not in cols:
            self.cursor.execute(f"ALTER TABLE users ADD COLUMN {name} {typ}")
            self.conn.commit()

    # ============ USERS ============
    def get_user(self, uid):
        self.cursor.execute(
            "SELECT balance, total_wagered, days_registered, invited_count, earned_ref "
            "FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        if not r:
            self.cursor.execute(
                "INSERT INTO users (user_id, balance, total_wagered, days_registered, "
                "invited_count, earned_ref, created_at) VALUES (?,?,?,?,?,?,?)",
                (uid, 0.0, 0.0, 1, 0, 0.0, int(time.time())))
            self.conn.commit()
            return 0.0, 0.0, 1, 0, 0.0
        return r

    def user_exists(self, uid):
        self.cursor.execute("SELECT 1 FROM users WHERE user_id=?", (uid,))
        return self.cursor.fetchone() is not None

    def set_username(self, uid, name):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET username=? WHERE user_id=?", (name, uid))
        self.conn.commit()

    def is_banned(self, uid):
        self.cursor.execute("SELECT is_banned FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return bool(r and r[0])

    def ban_user(self, uid):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET is_banned=1 WHERE user_id=?", (uid,))
        self.conn.commit()

    def unban_user(self, uid):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET is_banned=0 WHERE user_id=?", (uid,))
        self.conn.commit()

    def set_privacy(self, uid, private):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET is_private=? WHERE user_id=?",
                            (1 if private else 0, uid))
        self.conn.commit()

    def is_private(self, uid):
        self.cursor.execute("SELECT is_private FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return bool(r and r[0])

    # ============ BET (с проверкой баланса) ============
    def get_bet(self, uid):
        self.get_user(uid)
        self.cursor.execute("SELECT bet FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return r[0] if r and r[0] else 0.5

    def set_bet(self, uid, bet):
        """Возвращает True если ставка установлена, False если больше баланса."""
        self.get_user(uid)
        bet = float(bet)
        if bet <= 0:
            return False
        bal = self.get_balance(uid)
        if bet > bal:
            return False
        self.cursor.execute("UPDATE users SET bet=? WHERE user_id=?", (bet, uid))
        self.conn.commit()
        return True

    def get_bet_currency(self, uid):
        self.get_user(uid)
        self.cursor.execute("SELECT bet_currency FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return r[0] if r and r[0] else "usd"

    def set_bet_currency(self, uid, cur):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET bet_currency=? WHERE user_id=?",
                            (cur, uid))
        self.conn.commit()

    # ============ BALANCE ============
    def get_balance(self, uid):
        self.get_user(uid)
        self.cursor.execute("SELECT balance FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return r[0] if r else 0.0

    def update_balance(self, uid, amount):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET balance=balance+? WHERE user_id=?",
                            (amount, uid))
        self.conn.commit()

    def set_balance(self, uid, amount):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET balance=? WHERE user_id=?",
                            (amount, uid))
        self.conn.commit()

    def has_enough(self, uid, amount):
        return self.get_balance(uid) >= amount

    def get_stars_balance(self, uid):
        self.get_user(uid)
        self.cursor.execute("SELECT stars_balance FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return r[0] if r else 0.0

    def update_stars_balance(self, uid, amount):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET stars_balance=stars_balance+? "
                            "WHERE user_id=?", (amount, uid))
        self.conn.commit()

    def has_enough_stars(self, uid, amount):
        return self.get_stars_balance(uid) >= amount

    def swap_stars_to_usd(self, uid, stars, rate=0.013):
        self.get_user(uid)
        if stars <= 0 or self.get_stars_balance(uid) < stars:
            return 0.0
        usd = round(stars * rate, 2)
        self.update_stars_balance(uid, -stars)
        self.update_balance(uid, usd)
        return usd

    def get_bonus_balance(self, uid):
        self.get_user(uid)
        self.cursor.execute("SELECT bonus_balance FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return r[0] if r else 0.0

    def get_ref_balance(self, uid):
        self.get_user(uid)
        self.cursor.execute("SELECT earned_ref FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return r[0] if r else 0.0

    # ============ STATS ============
    def add_wager(self, uid, amount):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET total_wagered=total_wagered+? WHERE user_id=?",
                            (amount, uid))
        self.conn.commit()

    def add_win(self, uid, amount):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET total_won=total_won+? WHERE user_id=?",
                            (amount, uid))
        self.conn.commit()

    def add_loss(self, uid, amount):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET total_lost=total_lost+? WHERE user_id=?",
                            (amount, uid))
        self.conn.commit()

    def add_deposit(self, uid, amount):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET total_deposited=total_deposited+? "
                            "WHERE user_id=?", (amount, uid))
        self.conn.commit()

    def add_withdraw(self, uid, amount):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET total_withdrawn=total_withdrawn+? "
                            "WHERE user_id=?", (amount, uid))
        self.conn.commit()

    def inc_games(self, uid):
        self.get_user(uid)
        self.cursor.execute("UPDATE users SET games_played=games_played+1 "
                            "WHERE user_id=?", (uid,))
        self.conn.commit()

    def get_stats(self, uid):
        self.get_user(uid)
        self.cursor.execute(
            "SELECT balance, stars_balance, total_wagered, total_won, total_lost, "
            "total_deposited, total_withdrawn, games_played, days_registered, "
            "invited_count, earned_ref FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        return {
            "balance": r[0], "stars_balance": r[1], "total_wagered": r[2],
            "total_won": r[3], "total_lost": r[4], "total_deposited": r[5],
            "total_withdrawn": r[6], "games_played": r[7],
            "days_registered": r[8], "invited_count": r[9], "earned_ref": r[10],
        }

    def get_full_stats(self, uid):
        self.get_user(uid)
        self.cursor.execute("""
            SELECT balance, total_wagered, total_won, total_lost,
                   total_deposited, total_withdrawn, games_played,
                   days_registered, invited_count, earned_ref
            FROM users WHERE user_id=?
        """, (uid,))
        r = self.cursor.fetchone()
        return {
            "balance": r[0], "wagered": r[1], "won": r[2], "lost": r[3],
            "deposited": r[4], "withdrawn": r[5], "games": r[6],
            "days": r[7], "invited": r[8], "ref_earned": r[9],
        }

    # ============ VIP ============
    def get_vip_info(self, uid):
        s = self.get_stats(uid)
        turnover = s["total_wagered"]
        levels = [(0, "None", "⭐"), (5000, "Bronze", "🥉"),
                  (20000, "Silver", "🥈"), (50000, "Gold", "🥇"),
                  (100000, "Platinum", "💎"), (500000, "Diamond", "💠"),
                  (1000000, "MAX", "👑")]
        cur = levels[0]
        nxt = levels[1]
        for i, lvl in enumerate(levels):
            if turnover >= lvl[0]:
                cur = lvl
                nxt = levels[i + 1] if i + 1 < len(levels) else None
        progress = ((turnover - cur[0]) / (nxt[0] - cur[0]) * 100
                    if nxt else 100.0)
        return {"current": cur, "next": nxt, "progress": min(progress, 100.0)}

    # ============ GAMES ============
    def add_game(self, uid, gt, bet, win, mult, result=""):
        self.cursor.execute(
            "INSERT INTO games (user_id, game_type, bet, win, multiplier, result, "
            "created_at) VALUES (?,?,?,?,?,?,?)",
            (uid, gt, bet, win, mult, result, int(time.time())))
        self.conn.commit()

    def get_last_games(self, uid, limit=10):
        self.cursor.execute(
            "SELECT game_type, bet, win, multiplier, created_at FROM games "
            "WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit))
        return self.cursor.fetchall()

    def get_games_stats(self, uid):
        self.cursor.execute(
            "SELECT game_type, COUNT(*), "
            "SUM(CASE WHEN result='win' THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN result IN ('lose','penalty') THEN 1 ELSE 0 END), "
            "COALESCE(SUM(CASE WHEN result='win' THEN win ELSE 0 END),0), "
            "COALESCE(SUM(bet),0) FROM games WHERE user_id=? GROUP BY game_type",
            (uid,))
        out = {}
        for row in self.cursor.fetchall():
            gt, games, wins, losses, won, staked = row
            out[gt] = {"games": games or 0, "wins": wins or 0, "losses": losses or 0,
                       "won": round(won or 0, 2), "staked": round(staked or 0, 2),
                       "profit": round((won or 0) - (staked or 0), 2)}
        return out

    # ============ TRANSACTIONS ============
    def add_transaction(self, uid, t, m, amount, commission=0.0,
                        status="pending", ext=""):
        self.cursor.execute(
            "INSERT INTO transactions (user_id, type, method, amount, commission, "
            "status, external_id, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (uid, t, m, amount, commission, status, ext, int(time.time())))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_transactions(self, uid, limit=10):
        self.cursor.execute(
            "SELECT type, method, amount, commission, status, created_at "
            "FROM transactions WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (uid, limit))
        return self.cursor.fetchall()

    # ============ CHECKS ============
    def add_check(self, uid, amount, url):
        self.cursor.execute(
            "INSERT INTO checks (user_id, amount, check_url, created_at) VALUES (?,?,?,?)",
            (uid, amount, url, int(time.time())))
        self.conn.commit()

    def get_checks(self, uid, limit=10):
        self.cursor.execute(
            "SELECT amount, check_url, is_activated, created_at FROM checks "
            "WHERE user_id=? ORDER BY id DESC LIMIT ?", (uid, limit))
        return self.cursor.fetchall()

    # ============ PROMO ============
    def create_promo(self, code, amount, uses=1):
        self.cursor.execute(
            "INSERT OR REPLACE INTO promocodes (code, amount, uses_left, created_at) "
            "VALUES (?,?,?,?)", (code.upper(), amount, uses, int(time.time())))
        self.conn.commit()

    def use_promo(self, uid, code):
        code = code.upper()
        self.cursor.execute("SELECT amount, uses_left FROM promocodes WHERE code=?",
                            (code,))
        r = self.cursor.fetchone()
        if not r or r[1] <= 0:
            return 0.0
        self.cursor.execute("SELECT 1 FROM promo_uses WHERE user_id=? AND code=?",
                            (uid, code))
        if self.cursor.fetchone():
            return 0.0
        amount = r[0]
        self.cursor.execute("UPDATE promocodes SET uses_left=uses_left-1 WHERE code=?",
                            (code,))
        self.cursor.execute("INSERT INTO promo_uses (user_id, code, created_at) "
                            "VALUES (?,?,?)", (uid, code, int(time.time())))
        self.update_balance(uid, amount)
        self.conn.commit()
        return amount

    def can_take_bonus(self, uid):
        self.get_user(uid)
        self.cursor.execute("SELECT last_bonus FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        if not r:
            return True
        return (int(time.time()) - r[0]) >= 86400

    def take_bonus(self, uid, amount=1.0):
        self.get_user(uid)
        self.cursor.execute(
            "UPDATE users SET last_bonus=?, balance=balance+? WHERE user_id=?",
            (int(time.time()), amount, uid))
        self.conn.commit()

    # ============ REFERRALS ============
    def set_referrer(self, uid, ref_id):
        self.get_user(uid)
        self.cursor.execute("SELECT referrer_id FROM users WHERE user_id=?", (uid,))
        r = self.cursor.fetchone()
        if r and r[0] is None and uid != ref_id:
            self.cursor.execute("UPDATE users SET referrer_id=? WHERE user_id=?",
                                (ref_id, uid))
            self.cursor.execute("UPDATE users SET invited_count=invited_count+1 "
                                "WHERE user_id=?", (ref_id,))
            self.conn.commit()
            return True
        return False

    def add_ref_earnings(self, ref_id, amount):
        self.get_user(ref_id)
        self.cursor.execute(
            "UPDATE users SET earned_ref=earned_ref+?, balance=balance+? WHERE user_id=?",
            (amount, amount, ref_id))
        self.conn.commit()

    def get_referrals(self, uid, limit=50):
        self.cursor.execute(
            "SELECT user_id, username FROM users WHERE referrer_id=? LIMIT ?",
            (uid, limit))
        return self.cursor.fetchall()

    # ============ ACTIVE GAMES ============
    def set_active_game(self, uid, gt, state, bet, mult, data=""):
        self.cursor.execute(
            "INSERT OR REPLACE INTO active_games "
            "(user_id, game_type, state, bet, multiplier, data, created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (uid, gt, state, bet, mult, data, int(time.time())))
        self.conn.commit()

    def get_active_game(self, uid):
        self.cursor.execute(
            "SELECT game_type, state, bet, multiplier, data FROM active_games "
            "WHERE user_id=?", (uid,))
        return self.cursor.fetchone()

    def delete_active_game(self, uid):
        self.cursor.execute("DELETE FROM active_games WHERE user_id=?", (uid,))
        self.conn.commit()

    # ============ TOPS ============
    def get_top_balance(self, limit=10):
        self.cursor.execute(
            "SELECT user_id, username, balance FROM users "
            "ORDER BY balance DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def get_top_wagered(self, limit=10):
        self.cursor.execute(
            "SELECT user_id, username, total_wagered FROM users "
            "ORDER BY total_wagered DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    # ============ ADMIN ============
    def get_admin_stats(self, day_start):
        self.cursor.execute("SELECT COUNT(*) FROM users")
        uc = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COALESCE(SUM(total_wagered),0) FROM users")
        tt = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COALESCE(SUM(balance),0) FROM users")
        tb = self.cursor.fetchone()[0]
        self.cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(bet),0), COALESCE(SUM(win),0) "
            "FROM games WHERE created_at>=?", (day_start,))
        row = self.cursor.fetchone()
        self.cursor.execute(
            "SELECT COALESCE(SUM(amount),0), COUNT(*) FROM transactions "
            "WHERE type='deposit' AND status='success' AND created_at>=?",
            (day_start,))
        r = self.cursor.fetchone()
        self.cursor.execute(
            "SELECT COALESCE(SUM(amount),0), COUNT(*) FROM transactions "
            "WHERE type='withdraw' AND status='success' AND created_at>=?",
            (day_start,))
        w = self.cursor.fetchone()
        return {"users_count": uc, "total_turnover": tt, "total_balances": tb,
                "games_today": row[0], "turnover_today": row[1], "payout_today": row[2],
                "dep_today": r[0], "dep_count": r[1],
                "wd_today": w[0], "wd_count": w[1],
                "profit_today": row[1] - row[2]}

    def get_top_players_today(self, day_start, limit=10):
        self.cursor.execute(
            "SELECT user_id, COALESCE(SUM(bet),0) as t FROM games "
            "WHERE created_at>=? GROUP BY user_id ORDER BY t DESC LIMIT ?",
            (day_start, limit))
        return self.cursor.fetchall()

    # ============ TREASURY ============
    def get_treasury_manual(self):
        self.cursor.execute(
            "SELECT crypto_manual, xrocket_manual, updated_at FROM treasury WHERE id=1")
        r = self.cursor.fetchone()
        if not r:
            return {"crypto": 0.0, "xrocket": 0.0, "updated_at": 0}
        return {"crypto": r[0], "xrocket": r[1], "updated_at": r[2]}

    def add_treasury(self, platform, amount):
        self.get_treasury_manual()
        col = "crypto_manual" if platform == "crypto" else "xrocket_manual"
        self.cursor.execute(
            f"UPDATE treasury SET {col}={col}+?, updated_at=? WHERE id=1",
            (amount, int(time.time())))
        self.conn.commit()

    def set_treasury(self, platform, amount):
        self.get_treasury_manual()
        col = "crypto_manual" if platform == "crypto" else "xrocket_manual"
        self.cursor.execute(
            f"UPDATE treasury SET {col}=?, updated_at=? WHERE id=1",
            (amount, int(time.time())))
        self.conn.commit()

    def subtract_treasury(self, platform, amount):
        self.get_treasury_manual()
        col = "crypto_manual" if platform == "crypto" else "xrocket_manual"
        self.cursor.execute(
            f"UPDATE treasury SET {col}=MAX(0, {col}-?), updated_at=? WHERE id=1",
            (amount, int(time.time())))
        self.conn.commit()

    def close(self):
        self.conn.close()


db = Database()