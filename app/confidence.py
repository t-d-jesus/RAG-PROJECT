def calculate_confidence(
    sources: list[dict],
    distances: list[float],
) -> dict:
    if not sources or not distances:
        return {
            "level": "low",
            "score": 0.0,
            "reason": "Nenhuma fonte relevante foi encontrada.",
        }

    best_distance = min(distances)

    if best_distance <= 1.0:
        return {
            "level": "high",
            "score": 0.9,
            "reason": f"Melhor distância encontrada: {best_distance:.4f}",
        }

    if best_distance <= 1.5:
        return {
            "level": "medium",
            "score": 0.6,
            "reason": f"Melhor distância encontrada: {best_distance:.4f}",
        }

    return {
        "level": "low",
        "score": 0.3,
        "reason": f"Melhor distância alta: {best_distance:.4f}",
    }
