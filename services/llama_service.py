def get_llama_advice(sku_id: str, stock: int, days_left: int) -> str:
    # If your Ollama/Llama framework isn't hooked up yet, this clean string returns instantly
    if days_left < 5:
        return f"CRITICAL RUNBOOK ACTIVE FOR {sku_id}:\n1. Stock levels ({stock} units) are highly depleted.\n2. Scheduled warehouse delivery must be expedited within 48 hours.\n3. Turn off active marketing promos immediately to avoid consumer stockout friction."
    elif days_left < 12:
        return f"WARNING CONTEXT FOR {sku_id}:\n1. Current run-rate will deplete inventory in {days_left} days.\n2. Open procurement ticket with suppliers.\n3. Monitor daily velocity spikes."
    else:
        return f"SYSTEM BALANCED FOR {sku_id}:\n1. Inventory levels healthy.\n2. Current supply lane runway exceeds safety horizon windows.\n3. No manual fulfillment adjustments required."