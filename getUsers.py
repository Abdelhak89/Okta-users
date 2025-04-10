import boto3
import json
import csv
import requests
import certifi

def get_secret(secret_name, region_name):
    client = boto3.client("secretsmanager", region_name=region_name)
    try:
        response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        print(f"Erreur lors de la récupération du secret: {e}")
        raise e

    if 'SecretString' in response:
        return json.loads(response['SecretString'])
    else:
        return json.loads(response['SecretBinary'])

# --- CONFIGURATION ---
SECRET_NAME = "Prod/OKTA/DailyUsersDump/oktaApi"  # Remplace avec le nom ou l'ARN correct du secret
REGION_NAME = "us-east-1"   # Remplace par la région où se trouve le secret

# Récupération du secret
secrets = get_secret(SECRET_NAME, REGION_NAME)
print("Secret récupéré :", secrets)

# Extraction des valeurs du secret
okta_domain = secrets.get("base_url")
okta_token = secrets.get("Prod/OKTA/DailyUsersDump/oktaApi")

if not okta_domain or not okta_token:
    raise ValueError("Les informations 'okta_token' et/ou 'okta_domain' ne sont pas présentes dans le secret.")

# Préparation du header d'authentification (ajoute 'SSWS ' si nécessaire)
if not okta_token.startswith("SSWS "):
    okta_token = f"SSWS {okta_token}"

headers = {
    "Authorization": okta_token,
    "Accept": "application/json"
}

# --- APPEL API Okta ---
api_url = f"{okta_domain}/api/v1/users"
response = requests.get(api_url, headers=headers, verify=certifi.where())

# Vérifie le succès de l'appel API
if response.status_code != 200:
    raise ValueError(f"Échec de l'appel API: code {response.status_code}, réponse: {response.text}")

try:
    users = response.json()
except Exception as e:
    raise ValueError(f"Erreur lors du parsing de la réponse JSON: {e}")

# --- SAUVEGARDE JSON ---
with open("users.json", "w") as json_file:
    json.dump(users, json_file, indent=4)

# --- SAUVEGARDE CSV ---
with open("users.csv", "w", newline='') as csv_file:
    fieldnames = ["id", "firstName", "lastName", "email", "login", "status", "lastLogin"]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for user in users:
        writer.writerow({
            "id": user.get("id"),
            "firstName": user.get("profile", {}).get("firstName"),
            "lastName": user.get("profile", {}).get("lastName"),
            "email": user.get("profile", {}).get("email"),
            "login": user.get("profile", {}).get("login"),
            "status": user.get("status"),
            "lastLogin": user.get("lastLogin")
        })

print("✅ Données sauvegardées dans 'users.json' et 'users.csv'")
