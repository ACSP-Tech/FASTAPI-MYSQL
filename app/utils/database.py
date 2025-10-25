def normalize_mysql_url(url):
    """
    Converts a standard mysql:// URL to the asynchronous dialect
    required by SQLAlchemy and the 'mysqlclient' driver.
    
    The 'mysqlclient' driver works asynchronously via SQLAlchemy's 
    built-in asyncio mechanism.
    """
    # Convert mysql:// to mysql+mysqldb://
    if url.startswith("mysql://") and not url.startswith("mysql+mysqldb://"):
        url = url.replace("mysql://", "mysql+mysqldb://", 1)
        
    # Remove ?sslmode=require (common in cloud providers) - check if Aiven needs it
    if "?sslmode=" in url:
        url = url.split("?")[0]
    
    # Optional: Append charset settings if not present (often needed for MySQL)
    if "?" not in url:
        url += "?charset=utf8mb4"
    elif "charset=" not in url:
        url += "&charset=utf8mb4"

    return url