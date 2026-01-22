import sqlite3
import urllib.parse
import copy

DB_NAME = "renal_diet.db"

# --- GENERATION CONFIG ---
COOKING_SUFFIXES = {
    "es": {"raw": "", "boiled": " (Hervido)", "fried": " (Frito)", "roasted": " (Asado)", "battered": " (Rebozado)", "grilled": " (Plancha)"},
    "en": {"raw": "", "boiled": " (Boiled)", "fried": " (Fried)", "roasted": " (Roasted)", "battered": " (Battered)", "grilled": " (Grilled)"},
    "de": {"raw": "", "boiled": " (Gekocht)", "fried": " (Gebraten)", "roasted": " (Geröstet)", "battered": " (Paniert)", "grilled": " (Gegrillt)"},
    "fr": {"raw": "", "boiled": " (Bouilli)", "fried": " (Frit)", "roasted": " (Rôti)", "battered": " (Pané)", "grilled": " (Grillé)"},
    "pt": {"raw": "", "boiled": " (Cozido)", "fried": " (Frito)", "roasted": " (Assado)", "battered": " (Panado)", "grilled": " (Grelhado)"},
    "ja": {"raw": "", "boiled": " (茹で)", "fried": " (揚げ)", "roasted": " (ロースト)", "battered": " (衣揚げ)", "grilled": " (焼き)"}
}

def get_modifiers(method):
    mods = {"k_mult": 1.0, "p_mult": 1.0, "fat_add": 0.0, "carb_add": 0.0, "prot_mult": 1.0, "na_mult": 1.0}
    if method == "boiled":
        mods["k_mult"] = 0.6; mods["p_mult"] = 0.85; mods["na_mult"] = 0.9
    elif method == "fried":
        mods["fat_add"] = 12.0
    elif method == "roasted" or method == "grilled":
        mods["fat_add"] = 2.0; mods["k_mult"] = 1.1; mods["p_mult"] = 1.1; mods["prot_mult"] = 1.1
    elif method == "battered":
        mods["fat_add"] = 14.0; mods["carb_add"] = 15.0; mods["p_mult"] = 1.1
    return mods

def apply_method(food, method):
    if method == "raw": return food
    new_food = copy.deepcopy(food)
    mods = get_modifiers(method)
    
    for lang in COOKING_SUFFIXES:
        key = f"name_{lang}" if lang != "es" else "name"
        if key in new_food: new_food[key] += COOKING_SUFFIXES[lang][method]
        
    new_food["protein"] = round(new_food["protein"] * mods["prot_mult"], 1)
    new_food["fat"] = round(new_food["fat"] + mods["fat_add"], 1)
    new_food["potassium"] = round(new_food["potassium"] * mods["k_mult"], 0)
    new_food["phosphorus"] = round(new_food["phosphorus"] * mods["p_mult"], 0)
    new_food["salt"] = round(new_food["salt"] * mods["na_mult"], 2)
    new_food["calcium"] = round(new_food["calcium"], 0)
    
    
    # Specific fix for Potatoes visuals as per user request
    if "potato" in new_food['image_query']:
        if method == "fried": 
            new_food['image_query'] = "french fries"
        elif method == "boiled": 
            new_food['image_query'] = "boiled potatoes pot"
        elif method == "roasted": 
            new_food['image_query'] = "roasted potatoes oven"
        elif method == "grilled": 
            new_food['image_query'] = "grilled sliced potatoes"
        elif method == "battered": 
            new_food['image_query'] = "battered fried potato"
    else:
        new_food["image_query"] = f"{method} {new_food['image_query']}"
        
    return new_food

def get_image_url(query):
    base_url = "https://tse2.mm.bing.net/th"
    # Enforcing "real food", "close up", and "no people" to comply with user request
    refined_query = f"{query} fresh food close up photography no people -cartoon -illustration -clipart"
    params = {"q": refined_query, "w": "500", "h": "500", "c": "7", "rs": "1", "p": "0"}
    return f"{base_url}?{urllib.parse.urlencode(params)}"

BASE_DB = [
    {
        "category": "vegetables",
        "methods": ["raw", "boiled", "fried", "roasted", "grilled"],
        "items": [
            {"n":"Patata", "en":"Potato", "de":"Kartoffel", "fr":"Pomme de terre", "pt":"Batata", "ja":"ジャガイモ", "q": "potato", "p":2.0,"s":0.8,"f":0.1,"k":421,"ph":57,"sa":0.01,"ca":12},
            {"n":"Zanahoria", "en":"Carrot", "de":"Karotte", "fr":"Carotte", "pt":"Cenoura", "ja":"人参", "q": "carrot", "p":0.9,"s":4.7,"f":0.2,"k":320,"ph":35,"sa":0.06,"ca":33},
            {"n":"Espinacas", "en":"Spinach", "de":"Spinat", "fr":"Épinards", "pt":"Espinafre", "ja":"ほうれん草", "q": "spinach", "p":2.9,"s":0.4,"f":0.4,"k":558,"ph":49,"sa":0.07,"ca":99},
            {"n":"Brócoli", "en":"Broccoli", "de":"Brokkoli", "fr":"Brocoli", "pt":"Brócolis", "ja":"ブロッコリー", "q": "broccoli", "p":2.8,"s":1.7,"f":0.4,"k":316,"ph":66,"sa":0.03,"ca":47},
            {"n":"Coliflor", "en":"Cauliflower", "de":"Blumenkohl", "fr":"Chou-fleur", "pt":"Couve-flor", "ja":"カリフラワー", "q": "cauliflower", "p":1.9,"s":1.9,"f":0.3,"k":299,"ph":44,"sa":0.03,"ca":22},
            {"n":"Calabacín", "en":"Zucchini", "de":"Zucchini", "fr":"Courgette", "pt":"Abobrinha", "ja":"ズッキーニ", "q": "zucchini", "p":1.2,"s":2.5,"f":0.3,"k":261,"ph":38,"sa":0.01,"ca":16},
            {"n":"Berenjena", "en":"Eggplant", "de":"Aubergine", "fr":"Aubergine", "pt":"Beringela", "ja":"ナス", "q": "eggplant", "p":1.0,"s":3.5,"f":0.2,"k":229,"ph":24,"sa":0.01,"ca":9},
            {"n":"Pimiento Rojo", "en":"Red Pepper", "de":"Rote Paprika", "fr":"Poivron Rouge", "pt":"Pimento", "ja":"赤ピーマン", "q": "red pepper", "p":1.0,"s":4.2,"f":0.3,"k":211,"ph":26,"sa":0.01,"ca":7},
            {"n":"Pimiento Verde", "en":"Green Pepper", "de":"Grüne Paprika", "fr":"Poivron Vert", "pt":"Pimento Verde", "ja":"ピーマン", "q": "green pepper", "p":0.9,"s":2.4,"f":0.2,"k":175,"ph":20,"sa":0.01,"ca":10},
            {"n":"Tomate", "en":"Tomato", "de":"Tomate", "fr":"Tomate", "pt":"Tomate", "ja":"トマト", "q": "tomato", "p":0.9,"s":2.6,"f":0.2,"k":237,"ph":24,"sa":0.05,"ca":10},
            {"n":"Pepino", "en":"Cucumber", "de":"Gurke", "fr":"Concombre", "pt":"Pepino", "ja":"きゅうり", "q": "cucumber", "p":0.7,"s":1.7,"f":0.1,"k":147,"ph":24,"sa":0.01,"ca":16},
            {"n":"Cebolla", "en":"Onion", "de":"Zwiebel", "fr":"Oignon", "pt":"Cebola", "ja":"玉ねぎ", "q": "onion", "p":1.1,"s":4.2,"f":0.1,"k":146,"ph":29,"sa":0.01,"ca":23},
            {"n":"Ajo", "en":"Garlic", "de":"Knoblauch", "fr":"Ail", "pt":"Alho", "ja":"ニンニク", "q": "garlic", "p":6.4,"s":1.0,"f":0.5,"k":401,"ph":153,"sa":0.1,"ca":181},
            {"n":"Apio", "en":"Celery", "de":"Sellerie", "fr":"Céleri", "pt":"Aipo", "ja":"セロリ", "q": "celery", "p":0.7,"s":1.3,"f":0.2,"k":260,"ph":24,"sa":0.08,"ca":40},
            {"n":"Champiñones", "en":"Mushrooms", "de":"Pilze", "fr":"Champignons", "pt":"Cogumelos", "ja":"マッシュルーム", "q": "mushrooms", "p":3.1,"s":1.6,"f":0.3,"k":318,"ph":86,"sa":0.01,"ca":3},
            {"n":"Espárragos", "en":"Asparagus", "de":"Spargel", "fr":"Asperges", "pt":"Espargos", "ja":"アスパラガス", "q": "asparagus", "p":2.2,"s":1.9,"f":0.1,"k":202,"ph":52,"sa":0.01,"ca":24},
            {"n":"Judías Verdes", "en":"Green Beans", "de":"Grüne Bohnen", "fr":"Haricots Verts", "pt":"Feijão Verde", "ja":"インゲン", "q": "green beans", "p":1.8,"s":3.3,"f":0.1,"k":211,"ph":38,"sa":0.01,"ca":37},
            {"n":"Guisantes", "en":"Peas", "de":"Erbsen", "fr":"Petits Pois", "pt":"Ervilhas", "ja":"グリーンピース", "q": "peas", "p":5.4,"s":5.7,"f":0.4,"k":244,"ph":108,"sa":0.01,"ca":25},
            {"n":"Batata", "en":"Sweet Potato", "de":"Süßkartoffel", "fr":"Patate douce", "pt":"Batata Doce", "ja":"サツマイモ", "q": "sweet potato", "p":1.6,"s":4.2,"f":0.1,"k":337,"ph":47,"sa":0.05,"ca":30},
            {"n":"Calabaza", "en":"Pumpkin", "de":"Kürbis", "fr":"Citrouille", "pt":"Abóbora", "ja":"カボチャ", "q": "pumpkin", "p":1.0,"s":2.8,"f":0.1,"k":340,"ph":44,"sa":0.01,"ca":21},
            {"n":"Puerro", "en":"Leek", "de":"Lauch", "fr":"Poireau", "pt":"Alho-poró", "ja":"ネギ", "q": "leek", "p":1.5,"s":3.9,"f":0.3,"k":180,"ph":35,"sa":0.02,"ca":59},
            {"n":"Remolacha", "en":"Beetroot", "de":"Rote Bete", "fr":"Betterave", "pt":"Beterraba", "ja":"ビーツ", "q": "beetroot", "p":1.6,"s":6.8,"f":0.2,"k":325,"ph":40,"sa":0.08,"ca":16},
            {"n":"Rábano", "en":"Radish", "de":"Radieschen", "fr":"Radis", "pt":"Rabanete", "ja":"大根", "q": "radish", "p":0.7,"s":1.9,"f":0.1,"k":233,"ph":20,"sa":0.04,"ca":25},
            {"n":"Alcachofa", "en":"Artichoke", "de":"Artischocke", "fr":"Artichaut", "pt":"Alcachofra", "ja":"アーティチョーク", "q": "artichoke", "p":3.3,"s":1.0,"f":0.2,"k":370,"ph":90,"sa":0.1,"ca":44},
            {"n":"Kale", "en":"Kale", "de":"Grünkohl", "fr":"Chou frisé", "pt":"Couve Kale", "ja":"ケール", "q": "kale", "p":4.3,"s":2.3,"f":0.9,"k":491,"ph":92,"sa":0.04,"ca":150},
            {"n":"Bok Choy", "en":"Bok Choy", "de":"Pak Choi", "fr":"Bok Choy", "pt":"Bok Choy", "ja":"チンゲン菜", "q": "bok choy", "p":1.5,"s":1.2,"f":0.2,"k":252,"ph":37,"sa":0.06,"ca":105},
            {"n":"Okra", "en":"Okra", "de":"Okra", "fr":"Gombo", "pt":"Quiabo", "ja":"オクラ", "q": "okra", "p":1.9,"s":1.5,"f":0.2,"k":299,"ph":61,"sa":0.01,"ca":82},
            {"n":"Yuca", "en":"Cassava", "de":"Maniok", "fr":"Manioc", "pt":"Mandioca", "ja":"キャッサバ", "q": "cassava root", "p":1.4,"s":1.7,"f":0.3,"k":271,"ph":27,"sa":0.01,"ca":16},
            {"n":"Ñame", "en":"Yam", "de":"Yamswurzel", "fr":"Igname", "pt":"Inhame", "ja":"山芋", "q": "yam", "p":1.5,"s":0.5,"f":0.2,"k":816,"ph":55,"sa":0.01,"ca":17}, # High K!
            {"n":"Daikon", "en":"Daikon Radish", "de":"Daikon", "fr":"Daikon", "pt":"Nabo Daikon", "ja":"大根", "q": "daikon radish", "p":0.6,"s":2.5,"f":0.1,"k":227,"ph":23,"sa":0.02,"ca":27},
            {"n":"Hinojo", "en":"Fennel", "de":"Fenchel", "fr":"Fenouil", "pt":"Funcho", "ja":"フェンネル", "q": "fennel bulb", "p":1.2,"s":3.9,"f":0.2,"k":414,"ph":50,"sa":0.05,"ca":49},
            {"n":"Col de Bruselas", "en":"Brussels Sprouts", "de":"Rosenkohl", "fr":"Choux de Bruxelles", "pt":"Couve de Bruxelas", "ja":"芽キャベツ", "q": "brussels sprouts", "p":3.4,"s":2.2,"f":0.3,"k":389,"ph":69,"sa":0.02,"ca":42},
            {"n":"Maíz Dulce", "en":"Sweet Corn", "de":"Mais", "fr":"Maïs", "pt":"Milho", "ja":"とうもろこし", "q": "sweet corn", "p":3.2,"s":6.3,"f":1.2,"k":270,"ph":89,"sa":0.01,"ca":2},
            {"n":"Acelga", "en":"Chard", "de":"Mangold", "fr":"Blette", "pt":"Acelga", "ja":"フダンソウ", "q": "chard", "p":1.8,"s":1.1,"f":0.2,"k":379,"ph":46,"sa":0.2,"ca":51},
        ]
    },
    {
        "category": "fruits",
        "methods": ["raw"],
        "items": [
            {"n":"Manzana", "en":"Apple", "de":"Apfel", "fr":"Pomme", "pt":"Maçã", "ja":"リンゴ", "q": "apple", "p":0.3,"s":10.0,"f":0.2,"k":107,"ph":11,"sa":0.01,"ca":6},
            {"n":"Plátano", "en":"Banana", "de":"Banane", "fr":"Banane", "pt":"Banana", "ja":"バナナ", "q": "banana", "p":1.1,"s":12.2,"f":0.3,"k":358,"ph":27,"sa":0.01,"ca":5},
            {"n":"Pera", "en":"Pear", "de":"Birne", "fr":"Poire", "pt":"Pêra", "ja":"洋梨", "q": "pear", "p":0.4,"s":9.8,"f":0.1,"k":116,"ph":11,"sa":0.01,"ca":9},
            {"n":"Naranja", "en":"Orange", "de":"Orange", "fr":"Orange", "pt":"Laranja", "ja":"オレンジ", "q": "orange", "p":0.9,"s":9.4,"f":0.1,"k":181,"ph":14,"sa":0.0,"ca":40},
            {"n":"Mandarina", "en":"Tangerine", "de":"Mandarine", "fr":"Clémentine", "pt":"Mandarina", "ja":"みかん", "q": "tangerine", "p":0.8,"s":10.6,"f":0.3,"k":166,"ph":20,"sa":0.0,"ca":37},
            {"n":"Uvas", "en":"Grapes", "de":"Weintrauben", "fr":"Raisins", "pt":"Uvas", "ja":"ぶどう", "q": "grapes", "p":0.7,"s":16.0,"f":0.2,"k":191,"ph":20,"sa":0.01,"ca":10},
            {"n":"Melón", "en":"Melon", "de":"Melone", "fr":"Melon", "pt":"Melão", "ja":"メロン", "q": "cantaloupe", "p":0.8,"s":8.0,"f":0.2,"k":267,"ph":15,"sa":0.04,"ca":9},
            {"n":"Sandía", "en":"Watermelon", "de":"Wassermelone", "fr":"Pastèque", "pt":"Melancia", "ja":"スイカ", "q": "watermelon", "p":0.6,"s":6.0,"f":0.2,"k":112,"ph":11,"sa":0.01,"ca":7},
            {"n":"Piña", "en":"Pineapple", "de":"Ananas", "fr":"Ananas", "pt":"Abacaxi", "ja":"パイナップル", "q": "pineapple", "p":0.5,"s":9.9,"f":0.1,"k":109,"ph":8,"sa":0.01,"ca":13},
            {"n":"Kiwi", "en":"Kiwi", "de":"Kiwi", "fr":"Kiwi", "pt":"Kiwi", "ja":"キウイ", "q": "kiwi", "p":1.1,"s":9.0,"f":0.5,"k":312,"ph":34,"sa":0.01,"ca":34},
            {"n":"Fresas", "en":"Strawberries", "de":"Erdbeeren", "fr":"Fraises", "pt":"Morangos", "ja":"イチゴ", "q": "strawberries", "p":0.7,"s":4.9,"f":0.3,"k":153,"ph":24,"sa":0.01,"ca":16},
            {"n":"Arándanos", "en":"Blueberries", "de":"Blaubeeren", "fr":"Myrtilles", "pt":"Mirtilos", "ja":"ブルーベリー", "q": "blueberries", "p":0.7,"s":10.0,"f":0.3,"k":77,"ph":12,"sa":0.01,"ca":6},
            {"n":"Frambuesas", "en":"Raspberries", "de":"Himbeeren", "fr":"Framboises", "pt":"Framboesas", "ja":"ラズベリー", "q": "raspberries", "p":1.2,"s":4.4,"f":0.6,"k":151,"ph":29,"sa":0.01,"ca":25},
            {"n":"Moras", "en":"Blackberries", "de":"Brombeeren", "fr":"Mûres", "pt":"Amoras", "ja":"ブラックベリー", "q": "blackberries", "p":1.4,"s":4.9,"f":0.5,"k":162,"ph":22,"sa":0.01,"ca":29},
            {"n":"Limón", "en":"Lemon", "de":"Zitrone", "fr":"Citron", "pt":"Limão", "ja":"レモン", "q": "lemon", "p":1.1,"s":2.5,"f":0.3,"k":138,"ph":16,"sa":0.01,"ca":26},
            {"n":"Lima", "en":"Lime", "de":"Limette", "fr":"Citron Vert", "pt":"Lima", "ja":"ライム", "q": "lime", "p":0.7,"s":1.7,"f":0.2,"k":102,"ph":18,"sa":0.01,"ca":33},
            {"n":"Pomelo", "en":"Grapefruit", "de":"Grapefruit", "fr":"Pamplemousse", "pt":"Toranja", "ja":"グレープフルーツ", "q": "grapefruit", "p":0.7,"s":7.0,"f":0.1,"k":135,"ph":8,"sa":0.0,"ca":12},
            {"n":"Melocotón", "en":"Peach", "de":"Pfirsich", "fr":"Pêche", "pt":"Pêssego", "ja":"桃", "q": "peach", "p":0.9,"s":8.4,"f":0.3,"k":190,"ph":20,"sa":0.0,"ca":6},
            {"n":"Albaricoque", "en":"Apricot", "de":"Aprikose", "fr":"Abricot", "pt":"Damasco", "ja":"杏", "q": "apricot", "p":1.4,"s":9.0,"f":0.4,"k":259,"ph":23,"sa":0.01,"ca":13},
            {"n":"Nectarina", "en":"Nectarine", "de":"Nektarine", "fr":"Nectarine", "pt":"Nectarina", "ja":"ネクタリン", "q": "nectarine", "p":1.1,"s":10.6,"f":0.3,"k":201,"ph":26,"sa":0.0,"ca":6},
            {"n":"Ciruela", "en":"Plum", "de":"Pflaume", "fr":"Prune", "pt":"Ameixa", "ja":"プラム", "q": "plum", "p":0.7,"s":10.0,"f":0.3,"k":157,"ph":16,"sa":0.0,"ca":6},
            {"n":"Cereza", "en":"Cherry", "de":"Kirsche", "fr":"Cerise", "pt":"Cereja", "ja":"さくらんぼ", "q": "cherry", "p":1.1,"s":12.8,"f":0.2,"k":222,"ph":21,"sa":0.0,"ca":13},
            {"n":"Mango", "en":"Mango", "de":"Mango", "fr":"Mangue", "pt":"Manga", "ja":"マンゴー", "q": "mango", "p":0.8,"s":14.0,"f":0.4,"k":168,"ph":14,"sa":0.01,"ca":11},
            {"n":"Papaya", "en":"Papaya", "de":"Papaya", "fr":"Papaye", "pt":"Mamão", "ja":"パパイヤ", "q": "papaya", "p":0.5,"s":8.0,"f":0.3,"k":182,"ph":10,"sa":0.01,"ca":20},
            {"n":"Higos", "en":"Figs", "de":"Feigen", "fr":"Figues", "pt":"Figos", "ja":"イチジク", "q": "figs", "p":0.8,"s":16.0,"f":0.3,"k":232,"ph":14,"sa":0.01,"ca":35},
            {"n":"Granada", "en":"Pomegranate", "de":"Granatapfel", "fr":"Grenade", "pt":"Romã", "ja":"ザクロ", "q": "pomegranate", "p":1.7,"s":13.7,"f":1.2,"k":236,"ph":36,"sa":0.01,"ca":10},
            {"n":"Caqui", "en":"Persimmon", "de":"Kaki", "fr":"Kaki", "pt":"Dióspiro", "ja":"柿", "q": "persimmon", "p":0.6,"s":12.5,"f":0.2,"k":161,"ph":17,"sa":0.01,"ca":8},
            {"n":"Chirimoya", "en":"Cherimoya", "de":"Cherimoya", "fr":"Chérimole", "pt":"Anona", "ja":"チェリモヤ", "q": "cherimoya", "p":1.6,"s":17.7,"f":0.7,"k":287,"ph":26,"sa":0.01,"ca":10},
            {"n":"Aguacate", "en":"Avocado", "de":"Avocado", "fr":"Avocat", "pt":"Abacate", "ja":"アボカド", "q": "avocado", "p":2.0,"s":0.7,"f":15.0,"k":485,"ph":52,"sa":0.01,"ca":12},
            {"n":"Coco", "en":"Coconut", "de":"Kokosnuss", "fr":"Noix de Coco", "pt":"Coco", "ja":"ココナッツ", "q": "coconut", "p":3.3,"s":6.0,"f":33.0,"k":356,"ph":113,"sa":0.02,"ca":14},
            {"n":"Lichi", "en":"Lychee", "de":"Litschi", "fr":"Litchi", "pt":"Lichia", "ja":"ライチ", "q": "lychee", "p":0.8,"s":15.0,"f":0.4,"k":171,"ph":31,"sa":0.01,"ca":5},
            {"n":"Fruta del Dragón", "en":"Dragon Fruit", "de":"Drachenfrucht", "fr":"Fruit du Dragon", "pt":"Pitaia", "ja":"ドラゴンフルーツ", "q": "dragon fruit", "p":1.2,"s":9.0,"f":0.0,"k":272,"ph":22,"sa":0.0,"ca":10},
            {"n":"Durian", "en":"Durian", "de":"Durian", "fr":"Durian", "pt":"Durian", "ja":"ドリアン", "q": "durian", "p":1.5,"s":27.0,"f":5.3,"k":436,"ph":39,"sa":0.01,"ca":6},
            {"n":"Maracuyá", "en":"Passion Fruit", "de":"Maracuja", "fr":"Fruit de la Passion", "pt":"Maracujá", "ja":"パッションフルーツ", "q": "passion fruit", "p":2.2,"s":11.2,"f":0.7,"k":348,"ph":68,"sa":0.03,"ca":12},
            {"n":"Guayaba", "en":"Guava", "de":"Guave", "fr":"Goyave", "pt":"Goiaba", "ja":"グアバ", "q": "guava", "p":2.6,"s":9.0,"f":1.0,"k":417,"ph":40,"sa":0.01,"ca":18},
            {"n":"Dátiles", "en":"Dates", "de":"Datteln", "fr":"Dattes", "pt":"Tâmaras", "ja":"デーツ", "q": "dates fruit", "p":2.5,"s":63.0,"f":0.4,"k":656,"ph":62,"sa":0.01,"ca":39}, # Very High K
        ]
    },    
    {
        "category": "meat_poultry",
        "methods": ["raw", "boiled", "fried", "roasted", "grilled", "battered"],
        "items": [
            {"n":"Pollo (Pechuga)", "en":"Chicken Breast", "de":"Hähnchenbrust", "fr":"Blanc de Poulet", "pt":"Peito de Frango", "ja":"鶏胸肉", "q": "chicken breast", "p":23.0,"s":0.0,"f":1.2,"k":256,"ph":196,"sa":0.06,"ca":15},
            {"n":"Pollo (Muslo)", "en":"Chicken Thigh", "de":"Hähnchenschenkel", "fr":"Cuisse de Poulet", "pt":"Coxa de Frango", "ja":"鶏もも肉", "q": "chicken thigh", "p":19.7,"s":0.0,"f":10.9,"k":215,"ph":172,"sa":0.08,"ca":12},
            {"n":"Pollo (Alitas)", "en":"Chicken Wings", "de":"Hähnchenflügel", "fr":"Ailes de Poulet", "pt":"Asas de Frango", "ja":"手羽先", "q": "chicken wings", "p":18.0,"s":0.0,"f":16.0,"k":170,"ph":150,"sa":0.08,"ca":10},
            {"n":"Pavo", "en":"Turkey", "de":"Truthahn", "fr":"Dinde", "pt":"Peru", "ja":"七面鳥", "q": "turkey meat", "p":29.0,"s":0.0,"f":1.0,"k":290,"ph":210,"sa":0.06,"ca":16},
            {"n":"Pato", "en":"Duck", "de":"Ente", "fr":"Canard", "pt":"Pato", "ja":"鴨肉", "q": "duck meat", "p":19.0,"s":0.0,"f":28.0,"k":270,"ph":180,"sa":0.07,"ca":12},
            {"n":"Ternera (Solomillo)", "en":"Beef (Sirloin)", "de":"Rinderfilet", "fr":"Faux-filet", "pt":"Lombo de Vaca", "ja":"牛サーロイン", "q": "beef sirloin", "p":26.0,"s":0.0,"f":7.0,"k":318,"ph":192,"sa":0.05,"ca":18},
            {"n":"Ternera (Entrecot)", "en":"Beef (Ribeye)", "de":"Entrecôte", "fr":"Entrecôte", "pt":"Entrecosto", "ja":"リブアイ", "q": "ribeye steak", "p":24.0,"s":0.0,"f":18.0,"k":300,"ph":180,"sa":0.06,"ca":15},
            {"n":"Ternera (Picada)", "en":"Beef (Minced)", "de":"Hackfleisch", "fr":"Bœuf Haché", "pt":"Carne Picada", "ja":"牛挽肉", "q": "minced beef", "p":24.0,"s":0.0,"f":15.0,"k":280,"ph":170,"sa":0.07,"ca":15},
            {"n":"Cerdo (Lomo)", "en":"Pork Loin", "de":"Schweinelende", "fr":"Filet de Porc", "pt":"Lombo de Porco", "ja":"豚ロース", "q": "pork loin", "p":21.0,"s":0.0,"f":6.0,"k":360,"ph":212,"sa":0.06,"ca":7},
            {"n":"Cerdo (Chuleta)", "en":"Pork Chop", "de":"Kotelett", "fr":"Côtelette de Porc", "pt":"Costeleta de Porco", "ja":"ポークチョップ", "q": "pork chop", "p":20.0,"s":0.0,"f":12.0,"k":340,"ph":200,"sa":0.07,"ca":10},
            {"n":"Cerdo (Panceta)", "en":"Pork Belly", "de":"Schweinebauch", "fr":"Poitrine de Porc", "pt":"Barriga de Porco", "ja":"豚バラ", "q": "pork belly", "p":9.0,"s":0.0,"f":53.0,"k":185,"ph":100,"sa":0.05,"ca":5},
            {"n":"Cordero", "en":"Lamb", "de":"Lamm", "fr":"Agneau", "pt":"Cordeiro", "ja":"ラム肉", "q": "lamb meat", "p":25.0,"s":0.0,"f":21.0,"k":310,"ph":180,"sa":0.06,"ca":18},
            {"n":"Conejo", "en":"Rabbit", "de":"Kaninchen", "fr":"Lapin", "pt":"Coelho", "ja":"ウサギ肉", "q": "rabbit meat", "p":22.0,"s":0.0,"f":4.0,"k":330,"ph":220,"sa":0.05,"ca":20},
            {"n":"Codorniz", "en":"Quail", "de":"Wachtel", "fr":"Caille", "pt":"Codorniz", "ja":"ウズラ", "q": "quail meat", "p":22.0,"s":0.0,"f":5.0,"k":240,"ph":220,"sa":0.06,"ca":15},
            {"n":"Hígado (Ternera)", "en":"Liver (Beef)", "de":"Rinderleber", "fr":"Foie de Bœuf", "pt":"Fígado de Vaca", "ja":"牛レバー", "q": "beef liver", "p":20.0,"s":0.0,"f":3.6,"k":313,"ph":352,"sa":0.07,"ca":6},
            {"n":"Hígado (Pollo)", "en":"Liver (Chicken)", "de":"Hühnerleber", "fr":"Foie de Volaille", "pt":"Fígado de Frango", "ja":"鶏レバー", "q": "chicken liver", "p":17.0,"s":0.0,"f":4.8,"k":230,"ph":290,"sa":0.07,"ca":8},
            {"n":"Salchicha (Cerdo)", "en":"Sausage (Pork)", "de":"Bratwurst", "fr":"Saucisse", "pt":"Salsicha", "ja":"ソーセージ", "q": "pork sausage", "p":12.0,"s":1.0,"f":30.0,"k":200,"ph":170,"sa":2.0,"ca":20},
            {"n":"Chorizo", "en":"Chorizo", "de":"Chorizo", "fr":"Chorizo", "pt":"Chouriço", "ja":"チョリソー", "q": "chorizo", "p":22.0,"s":2.0,"f":30.0,"k":380,"ph":240,"sa":3.5,"ca":18},
            {"n":"Jamón Serrano", "en":"Cured Ham", "de":"Rohschinken", "fr":"Jambon Cru", "pt":"Presunto", "ja":"生ハム", "q": "cured ham", "p":30.0,"s":0.0,"f":16.0,"k":350,"ph":220,"sa":5.0,"ca":12},
            {"n":"Jamón York", "en":"Cooked Ham", "de":"Kochschinken", "fr":"Jambon Blanc", "pt":"Fiambre", "ja":"ハム", "q": "cooked ham", "p":19.0,"s":1.0,"f":3.0,"k":300,"ph":180,"sa":2.0,"ca":10},
        ]
    },    
    {
        "category": "fish",
        "methods": ["raw", "boiled", "fried", "roasted", "grilled", "battered"],
        "items": [
            {"n":"Salmón", "en":"Salmon", "de":"Lachs", "fr":"Saumon", "pt":"Salmão", "ja":"サーモン", "q": "salmon fillet", "p":20.0,"s":0.0,"f":13.0,"k":363,"ph":200,"sa":0.05,"ca":12},
            {"n":"Merluza", "en":"Hake", "de":"Seehecht", "fr":"Colin", "pt":"Pescada", "ja":"メルルーサ", "q": "hake fish", "p":17.0,"s":0.0,"f":1.9,"k":290,"ph":190,"sa":0.1,"ca":41},
            {"n":"Bacalao", "en":"Cod", "de":"Kabeljau", "fr":"Morue", "pt":"Bacalhau", "ja":"タラ", "q": "cod fish", "p":18.0,"s":0.0,"f":0.7,"k":413,"ph":185,"sa":0.1,"ca":16},
            {"n":"Atún", "en":"Tuna", "de":"Thunfisch", "fr":"Thon", "pt":"Atum", "ja":"マグロ", "q": "tuna steak", "p":23.0,"s":0.0,"f":1.0,"k":250,"ph":200,"sa":0.05,"ca":14},
            {"n":"Sardinas", "en":"Sardines", "de":"Sardinen", "fr":"Sardines", "pt":"Sardinhas", "ja":"イワシ", "q": "sardines", "p":24.0,"s":0.0,"f":11.0,"k":397,"ph":490,"sa":0.1,"ca":382},
            {"n":"Lenguado", "en":"Sole", "de":"Seezunge", "fr":"Sole", "pt":"Linguado", "ja":"ヒラメ", "q": "sole fish", "p":17.5,"s":0.0,"f":1.5,"k":305,"ph":185,"sa":0.1,"ca":20},
            {"n":"Dorada", "en":"Sea Bream", "de":"Dorade", "fr":"Dorade", "pt":"Dourada", "ja":"鯛", "q": "sea bream", "p":19.0,"s":0.0,"f":2.0,"k":350,"ph":210,"sa":0.1,"ca":25},
            {"n":"Lubina", "en":"Sea Bass", "de":"Wolfsbarsch", "fr":"Bar", "pt":"Robalo", "ja":"スズキ", "q": "sea bass", "p":18.0,"s":0.0,"f":2.0,"k":340,"ph":200,"sa":0.1,"ca":20},
            {"n":"Trucha", "en":"Trout", "de":"Forelle", "fr":"Truite", "pt":"Truta", "ja":"マス", "q": "trout fish", "p":20.0,"s":0.0,"f":3.0,"k":361,"ph":220,"sa":0.05,"ca":43},
            {"n":"Emperador", "en":"Swordfish", "de":"Schwertfisch", "fr":"Espadon", "pt":"Espadarte", "ja":"メカジキ", "q": "swordfish steak", "p":20.0,"s":0.0,"f":4.0,"k":290,"ph":200,"sa":0.1,"ca":10},
            {"n":"Rodaballo", "en":"Turbot", "de":"Steinbutt", "fr":"Turbot", "pt":"Pregado", "ja":"ヒラメ", "q": "turbot fish", "p":16.0,"s":0.0,"f":3.0,"k":290,"ph":200,"sa":0.1,"ca":20},
            {"n":"Rape", "en":"Monkfish", "de":"Seeteufel", "fr":"Lotte", "pt":"Tamboril", "ja":"アンコウ", "q": "monkfish", "p":15.0,"s":0.0,"f":0.6,"k":230,"ph":180,"sa":0.1,"ca":15},
            {"n":"Mero", "en":"Grouper", "de":"Zackenbarsch", "fr":"Mérou", "pt":"Garoupa", "ja":"ハタ", "q": "grouper fish", "p":19.0,"s":0.0,"f":1.0,"k":340,"ph":200,"sa":0.1,"ca":20},
            {"n":"Calamar", "en":"Squid", "de":"Tintenfisch", "fr":"Calamar", "pt":"Lula", "ja":"イカ", "q": "squid", "p":15.6,"s":0.0,"f":1.4,"k":246,"ph":221,"sa":0.1,"ca":32},
            {"n":"Sepia", "en":"Cuttlefish", "de":"Sepia", "fr":"Seiche", "pt":"Choco", "ja":"コウイカ", "q": "cuttlefish", "p":16.0,"s":0.0,"f":0.9,"k":300,"ph":250,"sa":0.4,"ca":100},
            {"n":"Pulpo", "en":"Octopus", "de":"Oktopus", "fr":"Poulpe", "pt":"Polvo", "ja":"タコ", "q": "octopus", "p":15.0,"s":0.0,"f":1.0,"k":350,"ph":180,"sa":0.4,"ca":106},
            {"n":"Gambas", "en":"Prawns", "de":"Garnelen", "fr":"Crevettes", "pt":"Gambas", "ja":"エビ", "q": "prawns", "p":20.3,"s":0.0,"f":1.7,"k":259,"ph":244,"sa":0.15,"ca":54},
            {"n":"Mejillones", "en":"Mussels", "de":"Muscheln", "fr":"Moules", "pt":"Mexilhões", "ja":"ムール貝", "q": "mussels", "p":11.9,"s":0.0,"f":2.2,"k":320,"ph":285,"sa":0.3,"ca":26},
            {"n":"Vieras", "en":"Scallops", "de":"Jakobsmuscheln", "fr":"Coquilles Saint-Jacques", "pt":"Vieiras", "ja":"ホタテ", "q": "scallops", "p":17.0,"s":0.0,"f":0.8,"k":320,"ph":300,"sa":0.4,"ca":40},
            {"n":"Almejas", "en":"Clams", "de":"Muscheln", "fr":"Palourdes", "pt":"Amêijoas", "ja":"アサリ", "q": "clams", "p":12.0,"s":0.0,"f":1.0,"k":300,"ph":200,"sa":0.5,"ca":40},
            {"n":"Ostras", "en":"Oysters", "de":"Austern", "fr":"Huîtres", "pt":"Ostras", "ja":"カキ", "q": "oysters", "p":9.0,"s":0.0,"f":2.0,"k":200,"ph":150,"sa":0.8,"ca":60},
            {"n":"Anchoas", "en":"Anchovies", "de":"Sardellen", "fr":"Anchois", "pt":"Anchovas", "ja":"アンチョビ", "q": "anchovies", "p":29.0,"s":0.0,"f":6.0,"k":500,"ph":300,"sa":3.0,"ca":147},
            {"n":"Arenque", "en":"Herring", "de":"Hering", "fr":"Hareng", "pt":"Arenque", "ja":"ニシン", "q": "herring fish", "p":18.0,"s":0.0,"f":17.0,"k":330,"ph":230,"sa":0.1,"ca":60},
            {"n":"Caballa", "en":"Mackerel", "de":"Makrele", "fr":"Maquereau", "pt":"Cavala", "ja":"サバ", "q": "mackerel", "p":19.0,"s":0.0,"f":14.0,"k":310,"ph":220,"sa":0.1,"ca":12},
            {"n":"Congrio", "en":"Conger Eel", "de":"Meeraal", "fr":"Congre", "pt":"Congro", "ja":"アナゴ", "q": "conger eel", "p":19.0,"s":0.0,"f":5.0,"k":280,"ph":200,"sa":0.1,"ca":20},
            {"n":"Gallo", "en":"Megrim", "de":"Scheefschnut", "fr":"Cardine", "pt":"Areeiro", "ja":"カレイ", "q": "flatfish", "p":17.0,"s":0.0,"f":1.0,"k":250,"ph":180,"sa":0.1,"ca":40},
            {"n":"Perca", "en":"Perch", "de":"Barsch", "fr":"Perche", "pt":"Perca", "ja":"パーチ", "q": "perch fish", "p":19.0,"s":0.0,"f":1.0,"k":270,"ph":190,"sa":0.1,"ca":80},
            {"n":"Salmonete", "en":"Red Mullet", "de":"Meerbarbe", "fr":"Rouget", "pt":"Salmonete", "ja":"ヒメジ", "q": "red mullet", "p":19.0,"s":0.0,"f":4.0,"k":330,"ph":220,"sa":0.1,"ca":30},
            {"n":"Boquerón", "en":"Fresh Anchovy", "de":"Sardelle (Frisch)", "fr":"Anchois (Frais)", "pt":"Biqueirão", "ja":"カタクチイワシ", "q": "fresh anchovy", "p":20.0,"s":0.0,"f":3.0,"k":300,"ph":200,"sa":0.1,"ca":50},
            {"n":"Anguila", "en":"Eel", "de":"Aal", "fr":"Anguille", "pt":"Enguia", "ja":"ウナギ", "q": "eel", "p":18.0,"s":0.0,"f":11.0,"k":230,"ph":220,"sa":0.1,"ca":20},
            {"n":"Caviar", "en":"Caviar", "de":"Kaviar", "fr":"Caviar", "pt":"Caviar", "ja":"キャビア", "q": "caviar", "p":25.0,"s":0.0,"f":18.0,"k":180,"ph":350,"sa":1.5,"ca":275},
        ]
    },    
    {
        "category": "grains_legumes",
        "methods": ["boiled"], # Grains/legumes usually just cooked/boiled. Fried rice exists but base is boiled.
        "items": [
            {"n":"Arroz Blanco", "en":"White Rice", "de":"Weißer Reis", "fr":"Riz Blanc", "pt":"Arroz Branco", "ja":"白米", "q": "white rice cooked", "p":2.7,"s":0.0,"f":0.3,"k":35,"ph":43,"sa":0.01,"ca":10},
            {"n":"Arroz Integral", "en":"Brown Rice", "de":"Brauner Reis", "fr":"Riz Brun", "pt":"Arroz Integral", "ja":"玄米", "q": "brown rice cooked", "p":2.6,"s":0.0,"f":0.9,"k":43,"ph":83,"sa":0.01,"ca":23},
            {"n":"Pasta", "en":"Pasta", "de":"Nudeln", "fr":"Pâtes", "pt":"Massa", "ja":"パスタ", "q": "pasta cooked", "p":5.0,"s":0.5,"f":1.1,"k":44,"ph":58,"sa":0.01,"ca":14},
            {"n":"Quinoa", "en":"Quinoa", "de":"Quinoa", "fr":"Quinoa", "pt":"Quinoa", "ja":"キヌア", "q": "quinoa cooked", "p":4.4,"s":0.0,"f":1.9,"k":172,"ph":152,"sa":0.01,"ca":17},
            {"n":"Lentejas", "en":"Lentils", "de":"Linsen", "fr":"Lentilles", "pt":"Lentilhas", "ja":"レンズ豆", "q": "lentils cooked", "p":9.0,"s":0.0,"f":0.4,"k":369,"ph":180,"sa":0.01,"ca":19},
            {"n":"Garbanzos", "en":"Chickpeas", "de":"Kichererbsen", "fr":"Pois Chiches", "pt":"Grão de Bico", "ja":"ひよこ豆", "q": "chickpeas cooked", "p":8.9,"s":0.0,"f":2.6,"k":291,"ph":168,"sa":0.01,"ca":49},
            {"n":"Judías Blancas", "en":"White Beans", "de":"Weiße Bohnen", "fr":"Haricots Blancs", "pt":"Feijão Branco", "ja":"白インゲン豆", "q": "white beans cooked", "p":9.0,"s":0.0,"f":0.5,"k":400,"ph":140,"sa":0.01,"ca":60},
            {"n":"Judías Negras", "en":"Black Beans", "de":"Schwarze Bohnen", "fr":"Haricots Noirs", "pt":"Feijão Preto", "ja":"黒豆", "q": "black beans cooked", "p":8.9,"s":0.0,"f":0.5,"k":355,"ph":140,"sa":0.01,"ca":27},
            {"n":"Soja", "en":"Soybeans", "de":"Sojabohnen", "fr":"Soja", "pt":"Soja", "ja":"大豆", "q": "soybeans cooked", "p":16.6,"s":3.0,"f":9.0,"k":515,"ph":245,"sa":0.01,"ca":102},
            {"n":"Mijo", "en":"Millet", "de":"Hirse", "fr":"Millet", "pt":"Painço", "ja":"キビ", "q": "millet cooked", "p":3.5,"s":0.0,"f":1.0,"k":62,"ph":100,"sa":0.01,"ca":3},
            {"n":"Bulgur", "en":"Bulgur", "de":"Bulgur", "fr":"Boulgour", "pt":"Bulgur", "ja":"ブルグル", "q": "bulgur cooked", "p":3.1,"s":0.0,"f":0.2,"k":68,"ph":40,"sa":0.01,"ca":10},
            {"n":"Cuscús", "en":"Couscous", "de":"Couscous", "fr":"Couscous", "pt":"Cuscuz", "ja":"クスクス", "q": "couscous cooked", "p":3.8,"s":0.0,"f":0.2,"k":58,"ph":44,"sa":0.01,"ca":8},
            {"n":"Avena", "en":"Oats", "de":"Hafer", "fr":"Avoine", "pt":"Aveia", "ja":"オートミール", "q": "oats", "p":16.9,"s":0.0,"f":6.9,"k":429,"ph":523,"sa":0.01,"ca":54},
            {"n":"Cebada", "en":"Barley", "de":"Gerste", "fr":"Orge", "pt":"Cevada", "ja":"大麦", "q": "barley cooked", "p":2.3,"s":0.0,"f":0.4,"k":93,"ph":54,"sa":0.01,"ca":11},
            {"n":"Centeno", "en":"Rye", "de":"Roggen", "fr":"Seigle", "pt":"Centeio", "ja":"ライ麦", "q": "rye grain", "p":10.3,"s":1.0,"f":1.6,"k":510,"ph":332,"sa":0.01,"ca":24},
        ]
    },
    {
        "category": "others",
        "methods": ["raw", "boiled", "fried"],
        "items": [
            {"n":"Huevo", "en":"Egg", "de":"Ei", "fr":"Œuf", "pt":"Ovo", "ja":"卵", "q": "egg", "p":12.5,"s":0.4,"f":10.0,"k":126,"ph":198,"sa":0.1,"ca":56},
        ]
    },

    {
        "category": "sweets_drinks",
        "methods": ["raw"],
        "items": [
             {"n":"Chocolate Negro", "en":"Dark Chocolate", "de":"Dunkle Schokolade", "fr":"Chocolat Noir", "pt":"Chocolate Preto", "ja":"ダークチョコレート", "q": "dark chocolate", "p":4.9,"s":24.0,"f":42.0,"k":715,"ph":308,"sa":0.02,"ca":73},
             {"n":"Chocolate con Leche", "en":"Milk Chocolate", "de":"Milchschokolade", "fr":"Chocolat au Lait", "pt":"Chocolate de Leite", "ja":"ミルクチョコレート", "q": "milk chocolate", "p":7.7,"s":51.0,"f":29.0,"k":372,"ph":216,"sa":0.2,"ca":189},
             {"n":"Galletas", "en":"Biscuits", "de":"Kekse", "fr":"Biscuits", "pt":"Bolachas", "ja":"ビスケット", "q": "biscuits", "p":7.0,"s":20.0,"f":12.0,"k":100,"ph":90,"sa":0.8,"ca":30},
             {"n":"Miel", "en":"Honey", "de":"Honig", "fr":"Miel", "pt":"Mel", "ja":"蜂蜜", "q": "honey", "p":0.3,"s":82.0,"f":0.0,"k":52,"ph":4,"sa":0.0,"ca":6},
             {"n":"Mermelada", "en":"Jam", "de":"Marmelade", "fr":"Confiture", "pt":"Compota", "ja":"ジャム", "q": "jam", "p":0.5,"s":60.0,"f":0.0,"k":80,"ph":10,"sa":0.0,"ca":15},
             {"n":"Azúcar", "en":"Sugar", "de":"Zucker", "fr":"Sucre", "pt":"Açúcar", "ja":"砂糖", "q": "white sugar", "p":0.0,"s":100.0,"f":0.0,"k":0,"ph":0,"sa":0.0,"ca":0},
             {"n":"Coca Cola", "en":"Cola", "de":"Cola", "fr":"Coca", "pt":"Coca", "ja":"コーラ", "q": "coca cola", "p":0.0,"s":10.6,"f":0.0,"k":0,"ph":15,"sa":0.01,"ca":2},
             {"n":"Zumo Naranja", "en":"Orange Juice", "de":"Orangensaft", "fr":"Jus d'Orange", "pt":"Sumo de Laranja", "ja":"オレンジジュース", "q": "orange juice", "p":0.7,"s":8.4,"f":0.2,"k":200,"ph":17,"sa":0.0,"ca":11},
             {"n":"Café", "en":"Coffee", "de":"Kaffee", "fr":"Café", "pt":"Café", "ja":"コーヒー", "q": "coffee cup", "p":0.1,"s":0.0,"f":0.0,"k":49,"ph":3,"sa":0.0,"ca":2},
             {"n":"Té", "en":"Tea", "de":"Tee", "fr":"Thé", "pt":"Chá", "ja":"お茶", "q": "tea cup", "p":0.0,"s":0.0,"f":0.0,"k":37,"ph":0,"sa":0.0,"ca":0},
             {"n":"Vino Tinto", "en":"Red Wine", "de":"Rotwein", "fr":"Vin Rouge", "pt":"Vinho Tinto", "ja":"赤ワイン", "q": "red wine", "p":0.2,"s":0.6,"f":0.0,"k":127,"ph":23,"sa":0.01,"ca":8},
             {"n":"Cerveza", "en":"Beer", "de":"Bier", "fr":"Bière", "pt":"Cerveja", "ja":"ビール", "q": "beer glass", "p":0.5,"s":3.6,"f":0.0,"k":27,"ph":14,"sa":0.01,"ca":4},
             {"n":"Turrón", "en":"Nougat", "de":"Nougat", "fr":"Nougat", "pt":"Torrão", "ja":"ヌガー", "q": "nougat", "p":12.0,"s":45.0,"f":30.0,"k":300,"ph":250,"sa":0.05,"ca":60},
             {"n":"Helado", "en":"Ice Cream", "de":"Eiscreme", "fr":"Glace", "pt":"Gelado", "ja":"アイスクリーム", "q": "ice cream scoop", "p":3.5,"s":21.0,"f":11.0,"k":199,"ph":105,"sa":0.08,"ca":128},
             {"n":"Gelatina", "en":"Jelly", "de":"Götterspeise", "fr":"Gelée", "pt":"Gelatina", "ja":"ゼリー", "q": "fruit jelly", "p":1.2,"s":14.0,"f":0.0,"k":10,"ph":5,"sa":0.02,"ca":3},
        ]
    }
]

def populate():
    print(f"Generating massive DB...")
    generated = []
    
    # 1. Procedural Categories
    for cat in BASE_DB:
        for item in cat["items"]:
            base = {k:v for k,v in item.items() if k not in ['n','en','de','fr','pt','ja','q','p','s','f','k','ph','sa','ca']}
            # Mapping short keys to full keys
            base.update({
                "name":item["n"], "name_en":item["en"], "name_de":item["de"], "name_fr":item["fr"], "name_pt":item["pt"], "name_ja":item["ja"],
                "image_query":item["q"],
                "protein":item["p"], "sugar":item["s"], "fat":item["f"], "potassium":item["k"], "phosphorus":item["ph"], "salt":item["sa"], "calcium":item["ca"]
            })
            
            for method in cat["methods"]:
                generated.append(apply_method(base, method))

    # 2. Fixed additions (Dairy, Oils, Nuts, Processed)
    simples = [
        ("Leche Entera", "Whole Milk", "Vollmilch", "Lait Entier", "Leite Gordo", "牛乳", "milk", 3.2, 4.8, 3.6, 150, 93, 0.1, 120),
        ("Leche Desnatada", "Skim Milk", "Magermilch", "Lait Écrémé", "Leite Magro", "無脂肪牛乳", "skim milk", 3.4, 5.0, 0.1, 156, 96, 0.1, 122),
        ("Yogur", "Yogurt", "Joghurt", "Yaourt", "Iogurte", "ヨーグルト", "yogurt", 3.5, 4.7, 3.3, 141, 135, 0.1, 140),
        ("Queso Fresco", "Fresh Cheese", "Frischkäse", "Fromage Frais", "Queijo Fresco", "フレッシュチーズ", "fresh cheese", 12.0, 3.0, 10.0, 180, 220, 0.5, 550),
        ("Queso Cheddar", "Cheddar", "Cheddar", "Cheddar", "Cheddar", "チェダー", "cheddar cheese", 25.0, 0.1, 33.0, 98, 512, 1.8, 721),
        ("Queso Parmesano", "Parmesan", "Parmesan", "Parmesan", "Parmesão", "パルメザン", "parmesan cheese", 35.0, 0.0, 29.0, 125, 694, 1.5, 1109),
        ("Queso Mozzarella", "Mozzarella", "Mozzarella", "Mozzarella", "Mozzarella", "モッツァレラ", "mozzarella ball", 18.0, 1.0, 17.0, 76, 354, 0.6, 505),
        ("Nueces", "Walnuts", "Walnüsse", "Noix", "Nozes", "くるみ", "walnuts", 15.0, 2.6, 65.0, 441, 346, 0.01, 98),
        ("Almendras", "Almonds", "Mandeln", "Amandes", "Amêndoas", "アーモンド", "almonds", 21.0, 4.0, 49.0, 705, 481, 0.01, 264),
        ("Pistachos", "Pistachios", "Pistazien", "Pistaches", "Pistaches", "ピスタチオ", "pistachios", 20.0, 7.0, 45.0, 1025, 490, 0.01, 105),
        ("Anacardos", "Cashews", "Cashewkerne", "Noix de cajou", "Caju", "カシューナッツ", "cashews", 18.0, 5.9, 44.0, 660, 593, 0.01, 37),
        ("Aceite de Oliva", "Olive Oil", "Olivenöl", "Huile d'Olive", "Azeite", "オリーブオイル", "olive oil", 0.0, 0.0, 100.0, 0, 0, 0.0, 0),
        ("Mantequilla", "Butter", "Butter", "Beurre", "Manteiga", "バター", "butter", 0.9, 0.1, 81.0, 24, 24, 0.01, 24),
        ("Mayonesa", "Mayonnaise", "Mayonnaise", "Mayonnaise", "Maionese", "マヨネーズ", "mayonnaise", 1.0, 1.0, 75.0, 20, 28, 0.6, 12),
        ("Tofu", "Tofu", "Tofu", "Tofu", "Tofu", "豆腐", "tofu block", 8.0, 0.5, 4.8, 121, 97, 0.01, 350),
        ("Seitán", "Seitan", "Seitan", "Seitan", "Seitan", "セイタン", "seitan wheat gluten", 75.0, 0.0, 1.9, 100, 260, 0.05, 142),
        ("Tempeh", "Tempeh", "Tempeh", "Tempeh", "Tempeh", "テンペ", "tempeh", 19.0, 0.0, 11.0, 412, 266, 0.01, 111),

        # --- ZUMOS (JUICES) ---
        ("Zumo de Naranja", "Orange Juice", "Orangensaft", "Jus d'Orange", "Sumo de Laranja", "オレンジジュース", "orange juice", 0.7, 8.4, 0.2, 200, 17, 0.0, 11),
        ("Zumo de Manzana", "Apple Juice", "Apfelsaft", "Jus de Pomme", "Sumo de Maçã", "リンゴジュース", "apple juice", 0.1, 9.6, 0.1, 101, 7, 0.0, 5),
        ("Zumo de Piña", "Pineapple Juice", "Ananassaft", "Jus d'Ananas", "Sumo de Abacaxi", "パイナップルジュース", "pineapple juice", 0.4, 12.0, 0.1, 130, 8, 0.0, 13),
        ("Zumo de Uva", "Grape Juice", "Traubensaft", "Jus de Raisin", "Sumo de Uva", "ブドウジュース", "grape juice", 0.4, 14.0, 0.1, 119, 12, 0.0, 9),
        ("Zumo de Tomate", "Tomato Juice", "Tomatensaft", "Jus de Tomate", "Sumo de Tomate", "トマトジュース", "tomato juice", 0.8, 2.6, 0.1, 217, 19, 0.05, 8),
        ("Zumo de Pomelo", "Grapefruit Juice", "Grapefruitsaft", "Jus de Pamplemousse", "Sumo de Toranja", "グレープフルーツジュース", "grapefruit juice", 0.5, 9.0, 0.1, 162, 15, 0.0, 9),
        ("Zumo de Zanahoria", "Carrot Juice", "Karottensaft", "Jus de Carotte", "Sumo de Cenoura", "人参ジュース", "carrot juice", 0.9, 3.9, 0.1, 292, 29, 0.04, 24),
        ("Zumo de Melocotón", "Peach Juice", "Pfirsichsaft", "Jus de Pêche", "Sumo de Pêssego", "桃ジュース", "peach juice", 0.4, 8.0, 0.1, 120, 12, 0.0, 5),
        ("Zumo de Pera", "Pear Juice", "Birnensaft", "Jus de Poire", "Sumo de Pêra", "洋梨ジュース", "pear juice", 0.2, 9.0, 0.1, 80, 8, 0.0, 6),
        ("Zumo de Arándanos", "Cranberry Juice", "Cranberrysaft", "Jus de Canneberge", "Sumo de Arando", "クランベリージュース", "cranberry juice", 0.0, 12.0, 0.0, 77, 13, 0.0, 5),
        ("Zumo de Mango", "Mango Juice", "Mangosaft", "Jus de Mangue", "Sumo de Manga", "マンゴージュース", "mango juice", 0.5, 13.0, 0.2, 110, 10, 0.0, 10),
        ("Zumo de Granada", "Pomegranate Juice", "Granatapfelsaft", "Jus de Grenade", "Sumo de Romã", "ザクロジュース", "pomegranate juice", 0.2, 13.0, 0.0, 214, 25, 0.0, 11),
        ("Zumo de Limón", "Lemon Juice", "Zitronensaft", "Jus de Citron", "Sumo de Limão", "レモン汁", "lemon juice", 0.4, 2.5, 0.0, 103, 8, 0.0, 7),
        ("Zumo de Lima", "Lime Juice", "Limettensaft", "Jus de Citron Vert", "Sumo de Lima", "ライム果汁", "lime juice", 0.4, 1.7, 0.0, 117, 10, 0.0, 10),
        ("Zumo Multifruita", "Multifruit Juice", "Multivitaminsaft", "Jus Multifruits", "Sumo Multifrutas", "ミックスジュース", "mixed fruit juice", 0.5, 11.0, 0.1, 150, 15, 0.0, 10),
        ("Limonada", "Lemonade", "Limonade", "Limonade", "Limonada", "レモネード", "lemonade", 0.1, 10.0, 0.0, 10, 2, 0.0, 2),

        # --- YOGURES Y LÁCTEOS FERMENTADOS ---
        ("Yogur Natural", "Natural Yogurt", "Naturjoghurt", "Yaourt Nature", "Iogurte Natural", "プレーンヨーグルト", "natural yogurt", 3.5, 4.7, 3.3, 155, 95, 0.05, 121),
        ("Yogur Griego", "Greek Yogurt", "Griechischer Joghurt", "Yaourt Grec", "Iogurte Grego", "ギリシャヨーグルト", "greek yogurt", 10.0, 3.0, 5.0, 141, 135, 0.04, 110),
        ("Yogur Desnatado", "Low-fat Yogurt", "Fettarmer Joghurt", "Yaourt 0%", "Iogurte Magro", "低脂肪ヨーグルト", "low fat yogurt", 5.3, 7.0, 0.1, 234, 137, 0.07, 183),
        ("Yogur de Fresa", "Strawberry Yogurt", "Erdbeerjoghurt", "Yaourt à la Fraise", "Iogurte de Morango", "イチゴヨーグルト", "strawberry yogurt", 3.0, 15.0, 2.5, 180, 100, 0.05, 110),
        ("Yogur de Vainilla", "Vanilla Yogurt", "Vanillejoghurt", "Yaourt Vanille", "Iogurte de Baunilha", "バニラヨーグルト", "vanilla yogurt", 3.2, 14.0, 2.8, 170, 95, 0.05, 110),
        ("Yogur de Coco", "Coconut Yogurt", "Kokosjoghurt", "Yaourt Coco", "Iogurte de Coco", "ココナッツヨーグルト", "coconut yogurt", 3.0, 12.0, 4.0, 160, 90, 0.05, 100),
        ("Yogur de Soja", "Soy Yogurt", "Sojajoghurt", "Yaourt au Soja", "Iogurte de Soja", "豆乳ヨーグルト", "soy yogurt", 4.0, 2.0, 2.0, 120, 50, 0.04, 120),
        ("Yogur Sin Lactosa", "Lactose-free Yogurt", "Laktosefreier Joghurt", "Yaourt Sans Lactose", "Iogurte Sem Lactose", "乳糖不使用ヨーグルト", "lactose free yogurt", 3.5, 4.7, 3.3, 155, 95, 0.05, 121),
        ("Kefir", "Kefir", "Kefir", "Kéfir", "Kefir", "ケフィア", "kefir drink", 3.0, 4.0, 3.0, 150, 100, 0.04, 120),
        ("Skyr", "Skyr", "Skyr", "Skyr", "Skyr", "スキール", "skyr yogurt", 11.0, 4.0, 0.2, 150, 140, 0.05, 110),
        ("Ayran", "Ayran", "Ayran", "Ayran", "Ayran", "アイラン", "ayran drink", 2.0, 1.5, 1.5, 80, 60, 0.5, 70),
        ("Petit Suisse", "Petit Suisse", "Fruchtzwerge", "Petit Suisse", "Petit Suisse", "プチスイス", "petit suisse", 7.0, 12.0, 3.0, 120, 100, 0.03, 90),
        ("Cuajada", "Curd", "Quark", "Caillé", "Coalhada", "凝乳", "curd", 4.0, 4.0, 5.0, 130, 100, 0.04, 140),
        ("Yogur Líquido", "Drinking Yogurt", "Trinkjoghurt", "Yaourt à Boire", "Iogurte Líquido", "飲むヨーグルト", "drinking yogurt", 3.0, 12.0, 1.5, 140, 90, 0.05, 110),
    ]
    
    for s in simples:
        generated.append({
            "name":s[0], "name_en":s[1], "name_de":s[2], "name_fr":s[3], "name_pt":s[4], "name_ja":s[5],
            "image_query":s[6], "protein":s[7], "sugar":s[8], "fat":s[9], "potassium":s[10], "phosphorus":s[11], "salt":s[12], "calcium":s[13]
        })
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM foods")
    
    data = []
    for i, f in enumerate(generated, 1):
        data.append((i, f["name"], f["name_en"], f["name_de"], f["name_fr"], f["name_pt"], f["name_ja"], 
                     get_image_url(f["image_query"]), f["protein"], f["sugar"], f["fat"], f["potassium"], f["phosphorus"], f["salt"], f["calcium"]))
        
    cursor.executemany('INSERT INTO foods VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', data)
    conn.commit()
    print(f"Generated {len(generated)} items.")
    conn.close()

if __name__ == "__main__":
    populate()
