def format_error(provider: str, resp) -> str:
    code, name, msg = "", "", ""

    if isinstance(resp, dict):
        err = resp.get("error") or {}
        if isinstance(err, dict):
            code = str(err.get("code", ""))
            name = err.get("name", "")
            msg = err.get("description", "") or err.get("message", "")
        else:
            msg = str(err)
        if not code:
            code = str(resp.get("status", "") or resp.get("statusCode", ""))
        if not name:
            name = resp.get("title", "")
        if not msg:
            msg = resp.get("detail", "") or resp.get("message", "")

        # Достаём errors из info (формат xRocket)
        info = resp.get("info", {}) or {}
        errors = info.get("errors", {}) or {}
        if errors:
            msg = "; ".join(
                f"{k}: {', '.join(v) if isinstance(v, list) else v}"
                for k, v in errors.items()
            )

    # ---------------- CRYPTOBOT ----------------
    if provider == "crypto":
        if name == "METHOD_DISABLED":
            return "🚧 <b>Способ оплаты временно отключён</b>\nПопробуйте xRocket."
        if name == "NOT_ENOUGH_COINS":
            return "⚠️ <b>У казино нет средств на вывод</b>\nПопробуйте xRocket."
        if name == "INSUFFICIENT_FUNDS":
            return "❌ Недостаточно средств."
        if name == "INVOICE_NOT_FOUND":
            return "❌ Счёт не найден."
        if name == "INVOICE_ALREADY_PAID":
            return "✅ Счёт уже оплачен."

    # ---------------- XROCKET ----------------
    if provider == "xrocket":
        low = (code + " " + name + " " + msg).lower()

        if "operation_disabled" in low or code == "403":
            return (
                "⚠️ <b>Вывод временно недоступен</b>\n\n"
                "Выплаты xRocket ещё не активированы.\n"
                "Обратитесь к администрации."
            )
        if "unauthorized" in low or code == "401":
            return "⚠️ Ошибка авторизации платёжки."

    # ---------------- ОБЩИЕ ----------------
    if code == "429":
        return "⏳ Слишком много запросов. Подождите минуту."
    if code in ("500", "502", "503"):
        return "⚠️ Сервис перегружен. Попробуйте позже."

    # ---------- ДИАГНОСТИКА (временно!) ----------
    return (
        f"❌ <b>Ошибка платёжной системы</b>\n\n"
        f"<code>provider={provider}\n"
        f"code={code}\n"
        f"name={name}\n"
        f"msg={msg[:200]}</code>"
    )