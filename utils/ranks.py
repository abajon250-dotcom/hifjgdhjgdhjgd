def get_user_rank(wagered: float) -> tuple[str, str, int]:
    ranks = [
        ("Рекрут I", 0),
        ("Рекрут II", 20),
        ("Рекрут III", 50),
        ("Рекрут IV", 70),
        ("Рекрут V", 100),
        ("Страж I", 200),
        ("Рыцарь I", 500),
        ("Герой I", 1000),
        ("Легенда I", 2500),
        ("Властелин I", 5000),
        ("Божество I", 10000),
        ("Титан", 15000)
    ]

    current_rank = "Рекрут I"
    next_rank = "Рекрут II"
    next_threshold = 20

    for i in range(len(ranks)):
        name, threshold = ranks[i]
        if wagered >= threshold:
            current_rank = name
            if i + 1 < len(ranks):
                next_rank = ranks[i + 1][0]
                next_threshold = ranks[i + 1][1]
            else:
                next_rank = "MAX"
                next_threshold = threshold

    if next_rank == "MAX":
        progress = 100
    else:
        prev_threshold = next(t for n, t in ranks if n == current_rank)
        if next_threshold == prev_threshold:
            progress = 100
        else:
            progress = int(((wagered - prev_threshold) / (next_threshold - prev_threshold)) * 100)
            progress = max(0, min(100, progress))

    return current_rank, next_rank, progress