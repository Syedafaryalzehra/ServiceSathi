import pyodbc
from flask import g

def search_services_by_category(category_keyword: str) -> list[dict]:
    """Search for available services or sellers by category name (e.g., driver, plumber, electrician).
    Returns a list of providers with their details.
    """
    from app import get_db_connection
    conn = get_db_connection()
    if not conn:
        return [{"error": "Database connection failed."}]
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.category_name, v.name, v.description, v.average_rating, v.price_per_hour, v.experience_years, v.seller_id, v.profile_picture
        FROM View_Category_Providers v
        JOIN Categories c ON v.category_id = c.category_id
        WHERE c.category_name LIKE ? OR v.description LIKE ?
    """, ('%' + category_keyword + '%', '%' + category_keyword + '%'))
    
    providers = cursor.fetchall()
    
    results = []
    ui_providers = []
    
    for p in providers:
        results.append({
            "category": p.category_name,
            "seller_name": p.name,
            "rating": float(p.average_rating) if p.average_rating else 0.0,
            "price_per_hour": float(p.price_per_hour),
            "experience_years": p.experience_years
        })
        ui_providers.append((
            p.name, p.description, float(p.average_rating) if p.average_rating else 0.0,
            float(p.price_per_hour), p.experience_years, p.seller_id, p.profile_picture
        ))
            
    conn.close()
    
    if not hasattr(g, 'bot_providers'):
        g.bot_providers = []
    g.bot_providers.extend(ui_providers)
    
    if not results:
        return [{"message": f"No providers currently available matching '{category_keyword}'."}]
        
    return results

def search_services_by_price(min_price: float, max_price: float) -> list[dict]:
    """Find sellers providing services within a specific price range per hour.
    Returns a list of providers and their service details.
    """
    from app import get_db_connection
    conn = get_db_connection()
    if not conn:
        return [{"error": "Database connection failed."}]
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.category_name, v.name, v.description, v.average_rating, v.price_per_hour, v.experience_years, v.seller_id, v.profile_picture
        FROM View_Category_Providers v
        JOIN Categories c ON v.category_id = c.category_id
        WHERE v.price_per_hour > ? AND v.price_per_hour < ?
    """, (min_price, max_price))
    providers = cursor.fetchall()
    
    results = []
    ui_providers = []
    for p in providers:
        results.append({
            "category": p.category_name,
            "seller_name": p.name,
            "rating": float(p.average_rating) if p.average_rating else 0.0,
            "price_per_hour": float(p.price_per_hour),
            "experience_years": p.experience_years
        })
        ui_providers.append((
            p.name, p.description, float(p.average_rating) if p.average_rating else 0.0,
            float(p.price_per_hour), p.experience_years, p.seller_id, p.profile_picture
        ))
        
    conn.close()
    
    if not hasattr(g, 'bot_providers'):
        g.bot_providers = []
    g.bot_providers.extend(ui_providers)
    
    if not results:
        return [{"message": f"No providers found with price between {min_price} and {max_price}."}]
        
    return results