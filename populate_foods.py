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
            new_food['image_query'] = "plate of crispy french fries"
        elif method == "boiled": 
            new_food['image_query'] = "boiled potatoes in a bowl"
        elif method == "roasted": 
            new_food['image_query'] = "roasted golden potatoes"
        elif method == "grilled": 
            new_food['image_query'] = "grilled potato slices with grill marks"
        elif method == "battered": 
            new_food['image_query'] = "battered fried potato wedges"
    else:
        # For all other foods, we include the method for visual variety
        # but with a clear photographic prefix
        if method != "raw":
            new_food["image_query"] = f"photo of {method} {new_food['image_query']} served on a plate"
        
    return new_food

def get_image_url(query):
    base_url = "https://tse2.mm.bing.net/th"
    # Over-the-top constraints to force real photos and avoid drawings/people
    # Emphasizing "real life photography" and "on a plate/table"
    refined_query = f"real life realistic high quality photography of {query} delicious food -person -human -man -woman -child -kid -cartoon -illustration -clipart -drawing -sketch -vector -graphic -logo -fake -3d -cgi -rendering"
    params = {"q": refined_query, "w": "500", "h": "500", "c": "7", "rs": "1", "p": "0"}
    return f"{base_url}?{urllib.parse.urlencode(params)}"

BASE_DB = [
    {
        "category": "vegetables",
        "methods": ["raw", "boiled", "fried", "roasted", "grilled"],
        "items": [
            {"n":"Zanahoria", "en":"Carrot", "de":"Karotte", "fr":"Carotte", "pt":"Cenoura", "ja":"人参", "q": "bunch of fresh carrots", "p":0.9,"s":4.7,"f":0.2,"k":320,"ph":35,"sa":0.06,"ca":33},
            {"n":"Espinacas", "en":"Spinach", "de":"Spinat", "fr":"Épinards", "pt":"Espinafre", "ja":"ほうれん草", "q": "fresh baby spinach leaves bowl", "p":2.9,"s":0.4,"f":0.4,"k":558,"ph":49,"sa":0.07,"ca":99},
            {"n":"Brócoli", "en":"Broccoli", "de":"Brokkoli", "fr":"Brocoli", "pt":"Brócolis", "ja":"ブロッコリー", "q": "fresh green broccoli head", "p":2.8,"s":1.7,"f":0.4,"k":316,"ph":66,"sa":0.03,"ca":47},
            {"n":"Coliflor", "en":"Cauliflower", "de":"Blumenkohl", "fr":"Chou-fleur", "pt":"Couve-flor", "ja":"カリフラワー", "q": "fresh white cauliflower head", "p":1.9,"s":1.9,"f":0.3,"k":299,"ph":44,"sa":0.03,"ca":22},
            {"n":"Calabacín", "en":"Zucchini", "de":"Zucchini", "fr":"Courgette", "pt":"Abobrinha", "ja":"ズッキーニ", "q": "fresh green zucchini squash", "p":1.2,"s":2.5,"f":0.3,"k":261,"ph":38,"sa":0.01,"ca":16},
            {"n":"Berenjena", "en":"Eggplant", "de":"Aubergine", "fr":"Aubergine", "pt":"Beringela", "ja":"ナス", "q": "fresh purple eggplant", "p":1.0,"s":3.5,"f":0.2,"k":229,"ph":24,"sa":0.01,"ca":9},
            {"n":"Pimiento Rojo", "en":"Red Pepper", "de":"Rote Paprika", "fr":"Poivron Rouge", "pt":"Pimento", "ja":"赤ピーマン", "q": "fresh red bell pepper", "p":1.0,"s":4.2,"f":0.3,"k":211,"ph":26,"sa":0.01,"ca":7},
            {"n":"Pimiento Verde", "en":"Green Pepper", "de":"Grüne Paprika", "fr":"Poivron Vert", "pt":"Pimento Verde", "ja":"ピーマン", "q": "fresh green bell pepper", "p":0.9,"s":2.4,"f":0.2,"k":175,"ph":20,"sa":0.01,"ca":10},
            {"n":"Tomate", "en":"Tomato", "de":"Tomate", "fr":"Tomate", "pt":"Tomate", "ja":"トマト", "q": "fresh red tomato", "p":0.9,"s":2.6,"f":0.2,"k":237,"ph":24,"sa":0.05,"ca":10},
            {"n":"Pepino", "en":"Cucumber", "de":"Gurke", "fr":"Concombre", "pt":"Pepino", "ja":"きゅうり", "q": "fresh green cucumber", "p":0.7,"s":1.7,"f":0.1,"k":147,"ph":24,"sa":0.01,"ca":16},
            {"n":"Cebolla", "en":"Onion", "de":"Zwiebel", "fr":"Oignon", "pt":"Cebola", "ja":"玉ねぎ", "q": "whole brown onion with skin", "p":1.1,"s":4.2,"f":0.1,"k":146,"ph":29,"sa":0.01,"ca":23},
            {"n":"Ajo", "en":"Garlic", "de":"Knoblauch", "fr":"Ail", "pt":"Alho", "ja":"ニンニク", "q": "whole garlic bulb", "p":6.4,"s":1.0,"f":0.5,"k":401,"ph":153,"sa":0.1,"ca":181},
            {"n":"Apio", "en":"Celery", "de":"Sellerie", "fr":"Céleri", "pt":"Aipo", "ja":"セロリ", "q": "fresh celery stalks bunch", "p":0.7,"s":1.3,"f":0.2,"k":260,"ph":24,"sa":0.08,"ca":40},
            {"n":"Champiñones", "en":"Mushrooms", "de":"Pilze", "fr":"Champignons", "pt":"Cogumelos", "ja":"マッシュルーム", "q": "fresh white mushrooms", "p":3.1,"s":1.6,"f":0.3,"k":318,"ph":86,"sa":0.01,"ca":3},
            {"n":"Espárragos", "en":"Asparagus", "de":"Spargel", "fr":"Asperges", "pt":"Espargos", "ja":"アスパラガス", "q": "asparagus", "p":2.2,"s":1.9,"f":0.1,"k":202,"ph":52,"sa":0.01,"ca":24},
            {"n":"Judías Verdes", "en":"Green Beans", "de":"Grüne Bohnen", "fr":"Haricots Verts", "pt":"Feijão Verde", "ja":"インゲン", "q": "green beans", "p":1.8,"s":3.3,"f":0.1,"k":211,"ph":38,"sa":0.01,"ca":37},
            {"n":"Guisantes", "en":"Peas", "de":"Erbsen", "fr":"Petits Pois", "pt":"Ervilhas", "ja":"グリーンピース", "q": "fresh green peas bowl", "p":5.4,"s":5.7,"f":0.4,"k":244,"ph":108,"sa":0.01,"ca":25},
            {"n":"Calabaza", "en":"Pumpkin", "de":"Kürbis", "fr":"Citrouille", "pt":"Abóbora", "ja":"カボチャ", "q": "fresh pumpkin sliced", "p":1.0,"s":2.8,"f":0.1,"k":340,"ph":44,"sa":0.01,"ca":21},
            {"n":"Puerro", "en":"Leek", "de":"Lauch", "fr":"Poireau", "pt":"Alho-poró", "ja":"ネギ", "q": "fresh green leek onion", "p":1.5,"s":3.9,"f":0.3,"k":180,"ph":35,"sa":0.02,"ca":59},
            {"n":"Remolacha", "en":"Beetroot", "de":"Rote Bete", "fr":"Betterave", "pt":"Beterraba", "ja":"ビーツ", "q": "fresh beetroot bulb purple", "p":1.6,"s":6.8,"f":0.2,"k":325,"ph":40,"sa":0.08,"ca":16},
            {"n":"Rábano", "en":"Radish", "de":"Radieschen", "fr":"Radis", "pt":"Rabanete", "ja":"大根", "q": "fresh red radish bulb", "p":0.7,"s":1.9,"f":0.1,"k":233,"ph":20,"sa":0.04,"ca":25},
            {"n":"Alcachofa", "en":"Artichoke", "de":"Artischocke", "fr":"Artichaut", "pt":"Alcachofra", "ja":"アーティチョーク", "q": "fresh green artichoke", "p":3.3,"s":1.0,"f":0.2,"k":370,"ph":90,"sa":0.1,"ca":44},
            {"n":"Kale", "en":"Kale", "de":"Grünkohl", "fr":"Chou frisé", "pt":"Couve Kale", "ja":"ケール", "q": "fresh green kale leaves", "p":4.3,"s":2.3,"f":0.9,"k":491,"ph":92,"sa":0.04,"ca":150},
            {"n":"Bok Choy", "en":"Bok Choy", "de":"Pak Choi", "fr":"Bok Choy", "pt":"Bok Choy", "ja":"チンゲン菜", "q": "fresh bok choy cabbage", "p":1.5,"s":1.2,"f":0.2,"k":252,"ph":37,"sa":0.06,"ca":105},
            {"n":"Okra", "en":"Okra", "de":"Okra", "fr":"Gombo", "pt":"Quiabo", "ja":"オクラ", "q": "fresh green okra pods", "p":1.9,"s":1.5,"f":0.2,"k":299,"ph":61,"sa":0.01,"ca":82},
            {"n":"Daikon", "en":"Daikon Radish", "de":"Daikon", "fr":"Daikon", "pt":"Nabo Daikon", "ja":"大根", "q": "raw daikon radish whole", "p":0.6,"s":2.5,"f":0.1,"k":227,"ph":23,"sa":0.02,"ca":27},
            {"n":"Hinojo", "en":"Fennel", "de":"Fenchel", "fr":"Fenouil", "pt":"Funcho", "ja":"フェンネル", "q": "fresh fennel bulb root", "p":1.2,"s":3.9,"f":0.2,"k":414,"ph":50,"sa":0.05,"ca":49},
            {"n":"Col de Bruselas", "en":"Brussels Sprouts", "de":"Rosenkohl", "fr":"Choux de Bruxelles", "pt":"Couve de Bruxelas", "ja":"芽キャベツ", "q": "fresh green brussels sprouts", "p":3.4,"s":2.2,"f":0.3,"k":389,"ph":69,"sa":0.02,"ca":42},
            {"n":"Maíz Dulce", "en":"Sweet Corn", "de":"Mais", "fr":"Maïs", "pt":"Milho", "ja":"とうもろこし", "q": "yellow sweet corn cob", "p":3.2,"s":6.3,"f":1.2,"k":270,"ph":89,"sa":0.01,"ca":2},
            {"n":"Acelga", "en":"Chard", "de":"Mangold", "fr":"Blette", "pt":"Acelga", "ja":"フダンソウ", "q": "fresh chard leaves green", "p":1.8,"s":1.1,"f":0.2,"k":379,"ph":46,"sa":0.2,"ca":51},
        ]
    },
    {
        "category": "tubers_spec,legumes_nuts_group",
        "methods": ["raw", "boiled", "fried", "roasted", "grilled"],
        "items": [
            {"n":"Patata", "en":"Potato", "de":"Kartoffel", "fr":"Pomme de terre", "pt":"Batata", "ja":"ジャガイモ", "q": "raw brown potato whole", "p":2.0,"s":0.8,"f":0.1,"k":421,"ph":57,"sa":0.01,"ca":12},
        ]
    },
    {
        "category": "tubers_spec",
        "methods": ["raw", "boiled", "fried", "roasted", "grilled"],
        "items": [
            {"n":"Batata", "en":"Sweet Potato", "de":"Süßkartoffel", "fr":"Patate douce", "pt":"Batata Doce", "ja":"サツマイモ", "q": "sweet potato", "p":1.6,"s":4.2,"f":0.1,"k":337,"ph":47,"sa":0.05,"ca":30},
            {"n":"Yuca", "en":"Cassava", "de":"Maniok", "fr":"Manioc", "pt":"Mandioca", "ja":"キャッサバ", "q": "raw cassava root", "p":1.4,"s":1.7,"f":0.3,"k":271,"ph":27,"sa":0.01,"ca":16},
            {"n":"Ñame", "en":"Yam", "de":"Yamswurzel", "fr":"Igname", "pt":"Inhame", "ja":"山芋", "q": "raw yam root", "p":1.5,"s":0.5,"f":0.2,"k":816,"ph":55,"sa":0.01,"ca":17}, # High K!
        ]
    },
    {
        "category": "fruits",
        "methods": ["raw"],
        "items": [
            {"n":"Manzana", "en":"Apple", "de":"Apfel", "fr":"Pomme", "pt":"Maçã", "ja":"リンゴ", "q": "fresh red apple isolated", "p":0.3,"s":10.0,"f":0.2,"k":107,"ph":11,"sa":0.01,"ca":6},
            {"n":"Plátano", "en":"Banana", "de":"Banane", "fr":"Banane", "pt":"Banana", "ja":"バナナ", "q": "fresh yellow banana bunch", "p":1.1,"s":12.2,"f":0.3,"k":358,"ph":27,"sa":0.01,"ca":5},
            {"n":"Pera", "en":"Pear", "de":"Birne", "fr":"Poire", "pt":"Pêra", "ja":"洋梨", "q": "fresh green pear isolated", "p":0.4,"s":9.8,"f":0.1,"k":116,"ph":11,"sa":0.01,"ca":9},
            {"n":"Naranja", "en":"Orange", "de":"Orange", "fr":"Orange", "pt":"Laranja", "ja":"オレンジ", "q": "fresh whole orange fruit", "p":0.9,"s":9.4,"f":0.1,"k":181,"ph":14,"sa":0.0,"ca":40},
            {"n":"Mandarina", "en":"Tangerine", "de":"Mandarine", "fr":"Clémentine", "pt":"Mandarina", "ja":"みかん", "q": "fresh tangerine fruit peeled", "p":0.8,"s":10.6,"f":0.3,"k":166,"ph":20,"sa":0.0,"ca":37},
            {"n":"Uvas", "en":"Grapes", "de":"Weintrauben", "fr":"Raisins", "pt":"Uvas", "ja":"ぶどう", "q": "bunch of purple grapes", "p":0.7,"s":16.0,"f":0.2,"k":191,"ph":20,"sa":0.01,"ca":10},
            {"n":"Melón", "en":"Melon", "de":"Melone", "fr":"Melon", "pt":"Melão", "ja":"メロン", "q": "fresh cantaloupe melon slice", "p":0.8,"s":8.0,"f":0.2,"k":267,"ph":15,"sa":0.04,"ca":9},
            {"n":"Sandía", "en":"Watermelon", "de":"Wassermelone", "fr":"Pastèque", "pt":"Melancia", "ja":"スイカ", "q": "fresh watermelon slice red", "p":0.6,"s":6.0,"f":0.2,"k":112,"ph":11,"sa":0.01,"ca":7},
            {"n":"Piña", "en":"Pineapple", "de":"Ananas", "fr":"Ananas", "pt":"Abacaxi", "ja":"パイナップル", "q": "fresh pineapple fruit whole", "p":0.5,"s":9.9,"f":0.1,"k":109,"ph":8,"sa":0.01,"ca":13},
            {"n":"Kiwi", "en":"Kiwi", "de":"Kiwi", "fr":"Kiwi", "pt":"Kiwi", "ja":"キウイ", "q": "fresh kiwi fruit sliced", "p":1.1,"s":9.0,"f":0.5,"k":312,"ph":34,"sa":0.01,"ca":34},
            {"n":"Fresas", "en":"Strawberries", "de":"Erdbeeren", "fr":"Fraises", "pt":"Morangos", "ja":"イチゴ", "q": "fresh red strawberries bowl", "p":0.7,"s":4.9,"f":0.3,"k":153,"ph":24,"sa":0.01,"ca":16},
            {"n":"Arándanos", "en":"Blueberries", "de":"Blaubeeren", "fr":"Myrtilles", "pt":"Mirtilos", "ja":"ブルーベリー", "q": "fresh blueberries bowl", "p":0.7,"s":10.0,"f":0.3,"k":77,"ph":12,"sa":0.01,"ca":6},
            {"n":"Frambuesas", "en":"Raspberries", "de":"Himbeeren", "fr":"Framboises", "pt":"Framboesas", "ja":"ラズベリー", "q": "fresh raspberries bowl", "p":1.2,"s":4.4,"f":0.6,"k":151,"ph":29,"sa":0.01,"ca":25},
            {"n":"Moras", "en":"Blackberries", "de":"Brombeeren", "fr":"Mûres", "pt":"Amoras", "ja":"ブラックベリー", "q": "fresh blackberries bowl", "p":1.4,"s":4.9,"f":0.5,"k":162,"ph":22,"sa":0.01,"ca":29},
            {"n":"Limón", "en":"Lemon", "de":"Zitrone", "fr":"Citron", "pt":"Limão", "ja":"レモン", "q": "fresh yellow lemon isolated", "p":1.1,"s":2.5,"f":0.3,"k":138,"ph":16,"sa":0.01,"ca":26},
            {"n":"Lima", "en":"Lime", "de":"Limette", "fr":"Citron Vert", "pt":"Lima", "ja":"ライム", "q": "fresh green lime isolated", "p":0.7,"s":1.7,"f":0.2,"k":102,"ph":18,"sa":0.01,"ca":33},
            {"n":"Pomelo", "en":"Grapefruit", "de":"Grapefruit", "fr":"Pamplemousse", "pt":"Toranja", "ja":"グレープフルーツ", "q": "fresh grapefruit halved red", "p":0.7,"s":7.0,"f":0.1,"k":135,"ph":8,"sa":0.0,"ca":12},
            {"n":"Melocotón", "en":"Peach", "de":"Pfirsich", "fr":"Pêche", "pt":"Pêssego", "ja":"桃", "q": "fresh ripe peach fruit", "p":0.9,"s":8.4,"f":0.3,"k":190,"ph":20,"sa":0.0,"ca":6},
            {"n":"Albaricoque", "en":"Apricot", "de":"Aprikose", "fr":"Abricot", "pt":"Damasco", "ja":"杏", "q": "fresh apricot fruit isolated", "p":1.4,"s":9.0,"f":0.4,"k":259,"ph":23,"sa":0.01,"ca":13},
            {"n":"Nectarina", "en":"Nectarine", "de":"Nektarine", "fr":"Nectarine", "pt":"Nectarina", "ja":"ネクタリン", "q": "fresh nectarine fruit isolated", "p":1.1,"s":10.6,"f":0.3,"k":201,"ph":26,"sa":0.0,"ca":6},
            {"n":"Ciruela", "en":"Plum", "de":"Pflaume", "fr":"Prune", "pt":"Ameixa", "ja":"プラム", "q": "fresh purple plum fruit", "p":0.7,"s":10.0,"f":0.3,"k":157,"ph":16,"sa":0.0,"ca":6},
            {"n":"Cereza", "en":"Cherry", "de":"Kirsche", "fr":"Cerise", "pt":"Cereja", "ja":"さくらんぼ", "q": "fresh red cherries bunch", "p":1.1,"s":12.8,"f":0.2,"k":222,"ph":21,"sa":0.0,"ca":13},
            {"n":"Mango", "en":"Mango", "de":"Mango", "fr":"Mangue", "pt":"Manga", "ja":"マンゴー", "q": "fresh ripe mango fruit", "p":0.8,"s":14.0,"f":0.4,"k":168,"ph":14,"sa":0.01,"ca":11},
            {"n":"Papaya", "en":"Papaya", "de":"Papaya", "fr":"Papaye", "pt":"Mamão", "ja":"パパイヤ", "q": "fresh papaya fruit halved", "p":0.5,"s":8.0,"f":0.3,"k":182,"ph":10,"sa":0.01,"ca":20},
            {"n":"Higos", "en":"Figs", "de":"Feigen", "fr":"Figues", "pt":"Figos", "ja":"イチジク", "q": "fresh figs fruit halved", "p":0.8,"s":16.0,"f":0.3,"k":232,"ph":14,"sa":0.01,"ca":35},
            {"n":"Granada", "en":"Pomegranate", "de":"Granatapfel", "fr":"Grenade", "pt":"Romã", "ja":"ザクロ", "q": "fresh pomegranate fruit opened", "p":1.7,"s":13.7,"f":1.2,"k":236,"ph":36,"sa":0.01,"ca":10},
            {"n":"Caqui", "en":"Persimmon", "de":"Kaki", "fr":"Kaki", "pt":"Dióspiro", "ja":"柿", "q": "fresh persimmon fruit isolated", "p":0.6,"s":12.5,"f":0.2,"k":161,"ph":17,"sa":0.01,"ca":8},
            {"n":"Chirimoya", "en":"Cherimoya", "de":"Cherimoya", "fr":"Chérimole", "pt":"Anona", "ja":"チェリモヤ", "q": "fresh cherimoya fruit halved", "p":1.6,"s":17.7,"f":0.7,"k":287,"ph":26,"sa":0.01,"ca":10},
            {"n":"Aguacate", "en":"Avocado", "de":"Avocado", "fr":"Avocat", "pt":"Abacate", "ja":"アボカド", "q": "fresh avocado halved with pit", "p":2.0,"s":0.7,"f":15.0,"k":485,"ph":52,"sa":0.01,"ca":12},
            {"n":"Coco", "en":"Coconut", "de":"Kokosnuss", "fr":"Noix de Coco", "pt":"Coco", "ja":"ココナッツ", "q": "fresh coconut fruit cracked open", "p":3.3,"s":6.0,"f":33.0,"k":356,"ph":113,"sa":0.02,"ca":14},
            {"n":"Lichi", "en":"Lychee", "de":"Litschi", "fr":"Litchi", "pt":"Lichia", "ja":"ライチ", "q": "fresh lychee fruit peeled", "p":0.8,"s":15.0,"f":0.4,"k":171,"ph":31,"sa":0.01,"ca":5},
            {"n":"Fruta del Dragón", "en":"Dragon Fruit", "de":"Drachenfrucht", "fr":"Fruit du Dragon", "pt":"Pitaia", "ja":"ドラゴンフルーツ", "q": "fresh dragon fruit sliced pink", "p":1.2,"s":9.0,"f":0.0,"k":272,"ph":22,"sa":0.0,"ca":10},
            {"n":"Durian", "en":"Durian", "de":"Durian", "fr":"Durian", "pt":"Durian", "ja":"ドリアン", "q": "fresh durian fruit opened", "p":1.5,"s":27.0,"f":5.3,"k":436,"ph":39,"sa":0.01,"ca":6},
            {"n":"Maracuyá", "en":"Passion Fruit", "de":"Maracuja", "fr":"Fruit de la Passion", "pt":"Maracujá", "ja":"パッションフルーツ", "q": "fresh passion fruit halved", "p":2.2,"s":11.2,"f":0.7,"k":348,"ph":68,"sa":0.03,"ca":12},
            {"n":"Guayaba", "en":"Guava", "de":"Guave", "fr":"Goyave", "pt":"Goiaba", "ja":"グアバ", "q": "fresh guava fruit isolated", "p":2.6,"s":9.0,"f":1.0,"k":417,"ph":40,"sa":0.01,"ca":18},
            {"n":"Dátiles", "en":"Dates", "de":"Datteln", "fr":"Dattes", "pt":"Tâmaras", "ja":"デーツ", "q": "fresh dried dates fruit bowl", "p":2.5,"s":63.0,"f":0.4,"k":656,"ph":62,"sa":0.01,"ca":39},
        ]
    },    
    {
        "category": "proteins",
        "methods": ["raw", "boiled", "fried", "roasted", "grilled", "battered"],
        "items": [
            {"n":"Pollo (Pechuga)", "en":"Chicken Breast", "de":"Hähnchenbrust", "fr":"Blanc de Poulet", "pt":"Peito de Frango", "ja":"鶏胸肉", "q": "raw chicken breast pocket", "p":23.0,"s":0.0,"f":1.2,"k":256,"ph":196,"sa":0.06,"ca":15},
            {"n":"Pollo (Muslo)", "en":"Chicken Thigh", "de":"Hähnchenschenkel", "fr":"Cuisse de Poulet", "pt":"Coxa de Frango", "ja":"鶏もも肉", "q": "raw chicken thigh bowl", "p":19.7,"s":0.0,"f":10.9,"k":215,"ph":172,"sa":0.08,"ca":12},
            {"n":"Pollo (Alitas)", "en":"Chicken Wings", "de":"Hähnchenflügel", "fr":"Ailes de Poulet", "pt":"Asas de Frango", "ja":"手羽先", "q": "raw chicken wings plate", "p":18.0,"s":0.0,"f":16.0,"k":170,"ph":150,"sa":0.08,"ca":10},
            {"n":"Pavo", "en":"Turkey", "de":"Truthahn", "fr":"Dinde", "pt":"Peru", "ja":"七面鳥", "q": "raw turkey breast fillet", "p":29.0,"s":0.0,"f":1.0,"k":290,"ph":210,"sa":0.06,"ca":16},
            {"n":"Pato", "en":"Duck", "de":"Ente", "fr":"Canard", "pt":"Pato", "ja":"鴨肉", "q": "raw duck breast fillet", "p":19.0,"s":0.0,"f":28.0,"k":270,"ph":180,"sa":0.07,"ca":12},
            {"n":"Ternera (Solomillo)", "en":"Beef (Sirloin)", "de":"Rinderfilet", "fr":"Faux-filet", "pt":"Lombo de Vaca", "ja":"牛サーロイン", "q": "raw beef sirloin steak", "p":26.0,"s":0.0,"f":7.0,"k":318,"ph":192,"sa":0.05,"ca":18},
            {"n":"Ternera (Entrecot)", "en":"Beef (Ribeye)", "de":"Entrecôte", "fr":"Entrecôte", "pt":"Entrecosto", "ja":"リブアイ", "q": "raw ribeye beef steak", "p":24.0,"s":0.0,"f":18.0,"k":300,"ph":180,"sa":0.06,"ca":15},
            {"n":"Ternera (Picada)", "en":"Beef (Minced)", "de":"Hackfleisch", "fr":"Bœuf Haché", "pt":"Carne Picada", "ja":"牛挽肉", "q": "raw ground minced beef", "p":24.0,"s":0.0,"f":15.0,"k":280,"ph":170,"sa":0.07,"ca":15},
            {"n":"Cerdo (Lomo)", "en":"Pork Loin", "de":"Schweinelende", "fr":"Filet de Porc", "pt":"Lombo de Porco", "ja":"豚ロース", "q": "raw pork loin roast", "p":21.0,"s":0.0,"f":6.0,"k":360,"ph":212,"sa":0.06,"ca":7},
            {"n":"Cerdo (Chuleta)", "en":"Pork Chop", "de":"Kotelett", "fr":"Côtelette de Porc", "pt":"Costeleta de Porco", "ja":"ポークチョップ", "q": "raw pork chop meat", "p":20.0,"s":0.0,"f":12.0,"k":340,"ph":200,"sa":0.07,"ca":10},
            {"n":"Cerdo (Panceta)", "en":"Pork Belly", "de":"Schweinebauch", "fr":"Poitrine de Porc", "pt":"Barriga de Porco", "ja":"豚バラ", "q": "raw pork belly slice", "p":9.0,"s":0.0,"f":53.0,"k":185,"ph":100,"sa":0.05,"ca":5},
            {"n":"Cordero", "en":"Lamb", "de":"Lamm", "fr":"Agneau", "pt":"Cordeiro", "ja":"ラム肉", "q": "raw lamb meat chop", "p":25.0,"s":0.0,"f":21.0,"k":310,"ph":180,"sa":0.06,"ca":18},
            {"n":"Conejo", "en":"Rabbit", "de":"Kaninchen", "fr":"Lapin", "pt":"Coelho", "ja":"ウサギ肉", "q": "raw rabbit meat", "p":22.0,"s":0.0,"f":4.0,"k":330,"ph":220,"sa":0.05,"ca":20},
            {"n":"Codorniz", "en":"Quail", "de":"Wachtel", "fr":"Caille", "pt":"Codorniz", "ja":"ウズラ", "q": "raw quail meat", "p":22.0,"s":0.0,"f":5.0,"k":240,"ph":220,"sa":0.06,"ca":15},
            {"n":"Hígado (Ternera)", "en":"Liver (Beef)", "de":"Rinderleber", "fr":"Foie de Bœuf", "pt":"Fígado de Vaca", "ja":"牛レバー", "q": "raw beef liver slice", "p":20.0,"s":0.0,"f":3.6,"k":313,"ph":352,"sa":0.07,"ca":6},
            {"n":"Hígado (Pollo)", "en":"Liver (Chicken)", "de":"Hühnerleber", "fr":"Foie de Volaille", "pt":"Fígado de Frango", "ja":"鶏レバー", "q": "raw chicken liver bowl", "p":17.0,"s":0.0,"f":4.8,"k":230,"ph":290,"sa":0.07,"ca":8},
            {"n":"Salchicha (Cerdo)", "en":"Sausage (Pork)", "de":"Bratwurst", "fr":"Saucisse", "pt":"Salsicha", "ja":"ソーセージ", "q": "pork sausages", "p":12.0,"s":1.0,"f":30.0,"k":200,"ph":170,"sa":2.0,"ca":20},
            {"n":"Chorizo", "en":"Chorizo", "de":"Chorizo", "fr":"Chorizo", "pt":"Chouriço", "ja":"チョリソー", "q": "spanish chorizo spicy", "p":22.0,"s":2.0,"f":30.0,"k":380,"ph":240,"sa":3.5,"ca":18},
            {"n":"Jamón Serrano", "en":"Cured Ham", "de":"Rohschinken", "fr":"Jambon Cru", "pt":"Presunto", "ja":"生ハム", "q": "spanish serrano ham slices", "p":30.0,"s":0.0,"f":16.0,"k":350,"ph":220,"sa":5.0,"ca":12},
            {"n":"Jamón York", "en":"Cooked Ham", "de":"Kochschinken", "fr":"Jambon Blanc", "pt":"Fiambre", "ja":"ハム", "q": "sliced deli cooked ham", "p":19.0,"s":1.0,"f":3.0,"k":300,"ph":180,"sa":2.0,"ca":10},
            {"n":"Huevo", "en":"Egg", "de":"Ei", "fr":"Œuf", "pt":"Ovo", "ja":"卵", "q": "fresh raw egg", "p":12.5,"s":0.4,"f":10.0,"k":126,"ph":198,"sa":0.1,"ca":56},
        ]
    },    
    {
        "category": "proteins",
        "methods": ["raw", "boiled", "fried", "roasted", "grilled", "battered"],
        "items": [
            {"n":"Salmón", "en":"Salmon", "de":"Lachs", "fr":"Saumon", "pt":"Salmão", "ja":"サーモン", "q": "fresh raw salmon fillet", "p":20.0,"s":0.0,"f":13.0,"k":363,"ph":200,"sa":0.05,"ca":12},
            {"n":"Merluza", "en":"Hake", "de":"Seehecht", "fr":"Colin", "pt":"Pescada", "ja":"メルルーサ", "q": "fresh raw hake fillet", "p":17.0,"s":0.0,"f":1.9,"k":290,"ph":190,"sa":0.1,"ca":41},
            {"n":"Bacalao", "en":"Cod", "de":"Kabeljau", "fr":"Morue", "pt":"Bacalhau", "ja":"タラ", "q": "fresh raw cod fillet", "p":18.0,"s":0.0,"f":0.7,"k":413,"ph":185,"sa":0.1,"ca":16},
            {"n":"Atún", "en":"Tuna", "de":"Thunfisch", "fr":"Thon", "pt":"Atum", "ja":"マグロ", "q": "fresh raw tuna steak", "p":23.0,"s":0.0,"f":1.0,"k":250,"ph":200,"sa":0.05,"ca":14},
            {"n":"Sardinas", "en":"Sardines", "de":"Sardinen", "fr":"Sardines", "pt":"Sardinhas", "ja":"イワシ", "q": "fresh raw whole sardines", "p":24.0,"s":0.0,"f":11.0,"k":397,"ph":490,"sa":0.1,"ca":382},
            {"n":"Lenguado", "en":"Sole", "de":"Seezunge", "fr":"Sole", "pt":"Linguado", "ja":"ヒラメ", "q": "fresh raw sole fish fillet", "p":17.5,"s":0.0,"f":1.5,"k":305,"ph":185,"sa":0.1,"ca":20},
            {"n":"Dorada", "en":"Sea Bream", "de":"Dorade", "fr":"Dorade", "pt":"Dourada", "ja":"鯛", "q": "fresh raw sea bream fish", "p":19.0,"s":0.0,"f":2.0,"k":350,"ph":210,"sa":0.1,"ca":25},
            {"n":"Lubina", "en":"Sea Bass", "de":"Wolfsbarsch", "fr":"Bar", "pt":"Robalo", "ja":"スズキ", "q": "fresh raw sea bass fish", "p":18.0,"s":0.0,"f":2.0,"k":340,"ph":200,"sa":0.1,"ca":20},
            {"n":"Trucha", "en":"Trout", "de":"Forelle", "fr":"Truite", "pt":"Truta", "ja":"マス", "q": "fresh raw trout fish", "p":20.0,"s":0.0,"f":3.0,"k":361,"ph":220,"sa":0.05,"ca":43},
            {"n":"Emperador", "en":"Swordfish", "de":"Schwertfisch", "fr":"Espadon", "pt":"Espadarte", "ja":"メカジキ", "q": "fresh raw swordfish steak", "p":20.0,"s":0.0,"f":4.0,"k":290,"ph":200,"sa":0.1,"ca":10},
            {"n":"Rodaballo", "en":"Turbot", "de":"Steinbutt", "fr":"Turbot", "pt":"Pregado", "ja":"ヒラメ", "q": "fresh raw turbot fish", "p":16.0,"s":0.0,"f":3.0,"k":290,"ph":200,"sa":0.1,"ca":20},
            {"n":"Rape", "en":"Monkfish", "de":"Seeteufel", "fr":"Lotte", "pt":"Tamboril", "ja":"アンコウ", "q": "fresh raw monkfish tail", "p":15.0,"s":0.0,"f":0.6,"k":230,"ph":180,"sa":0.1,"ca":15},
            {"n":"Mero", "en":"Grouper", "de":"Zackenbarsch", "fr":"Mérou", "pt":"Garoupa", "ja":"ハタ", "q": "fresh raw grouper fish fillet", "p":19.0,"s":0.0,"f":1.0,"k":340,"ph":200,"sa":0.1,"ca":20},
            {"n":"Calamar", "en":"Squid", "de":"Tintenfisch", "fr":"Calamar", "pt":"Lula", "ja":"イカ", "q": "fresh raw squid tubes", "p":15.6,"s":0.0,"f":1.4,"k":246,"ph":221,"sa":0.1,"ca":32},
            {"n":"Sepia", "en":"Cuttlefish", "de":"Seiche", "fr":"Seiche", "pt":"Choco", "ja":"コウイカ", "q": "fresh raw cuttlefish", "p":16.0,"s":0.0,"f":0.9,"k":300,"ph":250,"sa":0.4,"ca":100},
            {"n":"Pulpo", "en":"Octopus", "de":"Oktopus", "fr":"Poulpe", "pt":"Polvo", "ja":"タコ", "q": "fresh raw octopus tentacles", "p":15.0,"s":0.0,"f":1.0,"k":350,"ph":180,"sa":0.4,"ca":106},
            {"n":"Gambas", "en":"Prawns", "de":"Garnelen", "fr":"Crevettes", "pt":"Gambas", "ja":"エビ", "q": "fresh raw king prawns", "p":20.3,"s":0.0,"f":1.7,"k":259,"ph":244,"sa":0.15,"ca":54},
            {"n":"Mejillones", "en":"Mussels", "de":"Muscheln", "fr":"Moules", "pt":"Mexilhões", "ja":"ムール貝", "q": "fresh raw mussels in shell", "p":11.9,"s":0.0,"f":2.2,"k":320,"ph":285,"sa":0.3,"ca":26},
            {"n":"Vieras", "en":"Scallops", "de":"Jakobsmuscheln", "fr":"Coquilles Saint-Jacques", "pt":"Vieiras", "ja":"ホタテ", "q": "fresh raw sea scallops", "p":17.0,"s":0.0,"f":0.8,"k":320,"ph":300,"sa":0.4,"ca":40},
            {"n":"Almejas", "en":"Clams", "de":"Muscheln", "fr":"Palourdes", "pt":"Amêijoas", "ja":"アサリ", "q": "fresh raw clams in shell", "p":12.0,"s":0.0,"f":1.0,"k":300,"ph":200,"sa":0.5,"ca":40},
            {"n":"Ostras", "en":"Oysters", "de":"Austern", "fr":"Huîtres", "pt":"Ostras", "ja":"カキ", "q": "fresh raw oysters in shell", "p":9.0,"s":0.0,"f":2.0,"k":200,"ph":150,"sa":0.8,"ca":60},
            {"n":"Anchoas", "en":"Anchovies", "de":"Sardellen", "fr":"Anchois", "pt":"Anchovas", "ja":"アンチョビ", "q": "spanish salted anchovies fillets", "p":29.0,"s":0.0,"f":6.0,"k":500,"ph":300,"sa":3.0,"ca":147},
            {"n":"Arenque", "en":"Herring", "de":"Hering", "fr":"Hareng", "pt":"Arenque", "ja":"ニシン", "q": "fresh herring fish fillet", "p":18.0,"s":0.0,"f":17.0,"k":330,"ph":230,"sa":0.1,"ca":60},
            {"n":"Caballa", "en":"Mackerel", "de":"Makrele", "fr":"Maquereau", "pt":"Cavala", "ja":"サバ", "q": "fresh mackerel fish fillet", "p":19.0,"s":0.0,"f":14.0,"k":310,"ph":220,"sa":0.1,"ca":12},
            {"n":"Congrio", "en":"Conger Eel", "de":"Meeraal", "fr":"Congre", "pt":"Congro", "ja":"アナゴ", "q": "fresh raw conger eel", "p":19.0,"s":0.0,"f":5.0,"k":280,"ph":200,"sa":0.1,"ca":20},
            {"n":"Gallo", "en":"Megrim", "de":"Scheefschnut", "fr":"Cardine", "pt":"Areeiro", "ja":"カレイ", "q": "fresh megrim fish fillet", "p":17.0,"s":0.0,"f":1.0,"k":250,"ph":180,"sa":0.1,"ca":40},
            {"n":"Perca", "en":"Perch", "de":"Barsch", "fr":"Perche", "pt":"Perca", "ja":"パーチ", "q": "fresh perch fish fillet", "p":19.0,"s":0.0,"f":1.0,"k":270,"ph":190,"sa":0.1,"ca":80},
            {"n":"Salmonete", "en":"Red Mullet", "de":"Meerbarbe", "fr":"Rouget", "pt":"Salmonete", "ja":"ヒメジ", "q": "fresh red mullet fish", "p":19.0,"s":0.0,"f":4.0,"k":330,"ph":220,"sa":0.1,"ca":30},
            {"n":"Boquerón", "en":"Fresh Anchovy", "de":"Sardelle (Frisch)", "fr":"Anchois (Frais)", "pt":"Biqueirão", "ja":"カタクチイワシ", "q": "fresh whole anchovies raw", "p":20.0,"s":0.0,"f":3.0,"k":300,"ph":200,"sa":0.1,"ca":50},
            {"n":"Anguila", "en":"Eel", "de":"Aal", "fr":"Anguille", "pt":"Enguia", "ja":"ウナギ", "q": "fresh eel meat raw", "p":18.0,"s":0.0,"f":11.0,"k":230,"ph":220,"sa":0.1,"ca":20},
            {"n":"Caviar", "en":"Caviar", "de":"Kaviar", "fr":"Caviar", "pt":"Caviar", "ja":"キャビア", "q": "black sturgeon caviar tin", "p":25.0,"s":0.0,"f":18.0,"k":180,"ph":350,"sa":1.5,"ca":275},
        ]
    },    
    {
        "category": "legumes_nuts_group,legumes_spec",
        "methods": ["boiled"],
        "items": [
            {"n":"Quinoa", "en":"Quinoa", "de":"Quinoa", "fr":"Quinoa", "pt":"Quinoa", "ja":"キヌア", "q": "cooked quinoa bowl", "p":4.4,"s":0.0,"f":1.9,"k":172,"ph":152,"sa":0.01,"ca":17},
            {"n":"Lentejas", "en":"Lentils", "de":"Linsen", "fr":"Lentilles", "pt":"Lentilhas", "ja":"レンズ豆", "q": "cooked brown lentils bowl", "p":9.0,"s":0.0,"f":0.4,"k":369,"ph":180,"sa":0.01,"ca":19},
            {"n":"Garbanzos", "en":"Chickpeas", "de":"Kichererbsen", "fr":"Pois Chiches", "pt":"Grão de Bico", "ja":"ひよこ豆", "q": "cooked chickpeas bowl", "p":8.9,"s":0.0,"f":2.6,"k":291,"ph":168,"sa":0.01,"ca":49},
            {"n":"Judías Blancas", "en":"White Beans", "de":"Weiße Bohnen", "fr":"Haricots Blancs", "pt":"Feijão Branco", "ja":"白インゲン豆", "q": "cooked white beans bowl", "p":9.0,"s":0.0,"f":0.5,"k":400,"ph":140,"sa":0.01,"ca":60},
            {"n":"Judías Negras", "en":"Black Beans", "de":"Haricots Noirs", "fr":"Haricots Noirs", "pt":"Feijão Preto", "ja":"黒豆", "q": "cooked black beans bowl", "p":8.9,"s":0.0,"f":0.5,"k":355,"ph":140,"sa":0.01,"ca":27},
            {"n":"Soja", "en":"Soybeans", "de":"Sojabohnen", "fr":"Soja", "pt":"Soja", "ja":"大豆", "q": "cooked soybeans bowl", "p":16.6,"s":3.0,"f":9.0,"k":515,"ph":245,"sa":0.01,"ca":102},
        ]
    },
    {
        "category": "carbs",
        "methods": ["boiled"],
        "items": [
            {"n":"Arroz Blanco", "en":"White Rice", "de":"Weißer Reis", "fr":"Riz Blanc", "pt":"Arroz Branco", "ja":"白米", "q": "bowl of white rice", "p":2.7,"s":0.0,"f":0.3,"k":35,"ph":43,"sa":0.01,"ca":10},
            {"n":"Arroz Integral", "en":"Brown Rice", "de":"Brauner Reis", "fr":"Riz Brun", "pt":"Arroz Integral", "ja":"玄米", "q": "bowl of brown rice", "p":2.6,"s":0.0,"f":0.9,"k":43,"ph":83,"sa":0.01,"ca":23},
            {"n":"Espaguetis", "en":"Spaghetti", "de":"Spaghetti", "fr":"Spaghetti", "pt":"Esparguete", "ja":"スパゲッティ", "q": "cooked spaghetti pasta", "p":5.0,"s":0.5,"f":1.1,"k":44,"ph":58,"sa":0.01,"ca":14},
            {"n":"Macarrones", "en":"Macaroni", "de":"Makkaroni", "fr":"Macaroni", "pt":"Macarrão", "ja":"マカロニ", "q": "cooked macaroni pasta", "p":5.0,"s":0.5,"f":1.1,"k":44,"ph":58,"sa":0.01,"ca":14},
            {"n":"Tallarines", "en":"Noodles", "de":"Nudeln", "fr":"Nouilles", "pt":"Talharim", "ja":"麺", "q": "cooked noodles", "p":4.5,"s":0.2,"f":0.5,"k":30,"ph":40,"sa":0.01,"ca":10},
            {"n":"Pasta Integral", "en":"Whole Wheat Pasta", "de":"Vollkornnudeln", "fr":"Pâtes Complètes", "pt":"Massa Integral", "ja":"全粒粉パスタ", "q": "cooked whole wheat pasta", "p":5.3,"s":0.5,"f":1.3,"k":115,"ph":140,"sa":0.01,"ca":18},
            {"n":"Pasta al Huevo", "en":"Egg Pasta", "de":"Eiernudeln", "fr":"Pâtes aux Œufs", "pt":"Massa de Ovo", "ja":"卵パスタ", "q": "cooked egg pasta", "p":6.5,"s":0.2,"f":3.0,"k":60,"ph":90,"sa":0.03,"ca":20},
            {"n":"Pasta Sin Gluten", "en":"Gluten Free Pasta", "de":"Glutenfreie Nudeln", "fr":"Pâtes Sans Gluten", "pt":"Massa Sem Glúten", "ja":"グルテンフリーパスタ", "q": "cooked gluten free rice pasta", "p":3.0,"s":0.5,"f":1.0,"k":80,"ph":70,"sa":0.01,"ca":10},
            {"n":"Gnocchi", "en":"Gnocchi", "de":"Gnocchi", "fr":"Gnocchi", "pt":"Nhoque", "ja":"ニョッキ", "q": "cooked potato gnocchi", "p":3.5,"s":0.5,"f":0.5,"k":200,"ph":60,"sa":0.3,"ca":10},
            {"n":"Lasaña", "en":"Lasagna Sheets", "de":"Lasagneblätter", "fr":"Feuilles de Lasagne", "pt":"Folhas de Lasanha", "ja":"ラザニア", "q": "cooked lasagna pasta sheets", "p":5.0,"s":0.5,"f":1.1,"k":44,"ph":58,"sa":0.01,"ca":14},
            {"n":"Cuscús", "en":"Couscous", "de":"Couscous", "fr":"Couscous", "pt":"Cuscuz", "ja":"クスクス", "q": "cooked couscous", "p":3.8,"s":0.0,"f":0.2,"k":58,"ph":44,"sa":0.01,"ca":8},
            {"n":"Bulgur", "en":"Bulgur", "de":"Bulgur", "fr":"Boulgour", "pt":"Bulgur", "ja":"ブルグル", "q": "cooked bulgur", "p":3.1,"s":0.0,"f":0.2,"k":68,"ph":40,"sa":0.01,"ca":10},
            {"n":"Mijo", "en":"Millet", "de":"Hirse", "fr":"Millet", "pt":"Painço", "ja":"キビ", "q": "cooked millet", "p":3.5,"s":0.0,"f":1.0,"k":62,"ph":100,"sa":0.01,"ca":3},
            {"n":"Avena", "en":"Oats", "de":"Hafer", "fr":"Avoine", "pt":"Aveia", "ja":"オートミール", "q": "dry oat flakes", "p":16.9,"s":0.0,"f":6.9,"k":429,"ph":523,"sa":0.01,"ca":54},
            {"n":"Cebada", "en":"Barley", "de":"Gerste", "fr":"Orge", "pt":"Cevada", "ja":"大麦", "q": "cooked barley", "p":2.3,"s":0.0,"f":0.4,"k":93,"ph":54,"sa":0.01,"ca":11},
            {"n":"Centeno", "en":"Rye", "de":"Roggen", "fr":"Seigle", "pt":"Centeio", "ja":"ライ麦", "q": "rye bread slices", "p":10.3,"s":1.0,"f":1.6,"k":510,"ph":332,"sa":0.01,"ca":24},
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
            base.update({
                "name":item["n"], "name_en":item["en"], "name_de":item["de"], "name_fr":item["fr"], "name_pt":item["pt"], "name_ja":item["ja"],
                "image_query":item["q"],
                "protein":item["p"], "sugar":item["s"], "fat":item["f"], "potassium":item["k"], "phosphorus":item["ph"], "salt":item["sa"], "calcium":item["ca"],
                "category": cat["category"]
            })
            for method in cat["methods"]:
                generated.append(apply_method(base, method))

    # 2. Fixed additions
    def make_item(cat, n, en, de, fr, pt, ja, q, p, s, f, k, ph, sa, ca):
        return {
            "name":n, "name_en":en, "name_de":de, "name_fr":fr, "name_pt":pt, "name_ja":ja,
            "image_query":q, "protein":p, "sugar":s, "fat":f, "potassium":k, "phosphorus":ph, "salt":sa, "calcium":ca,
            "category": cat
        }

    # Dairy
    generated.append(make_item("dairy", "Leche Entera", "Whole Milk", "Vollmilch", "Lait Entier", "Leite Gordo", "牛乳", "glass of fresh whole milk", 3.2, 4.8, 3.6, 150, 93, 0.1, 120))
    generated.append(make_item("dairy", "Leche Desnatada", "Skim Milk", "Magermilch", "Lait Écrémé", "Leite Magro", "無脂肪牛乳", "glass of skim milk", 3.4, 5.0, 0.1, 156, 96, 0.1, 122))
    generated.append(make_item("dairy", "Yogur Natural", "Natural Yogurt", "Naturjoghurt", "Yaourt Nature", "Iogurte Natural", "プレーンヨーグルト", "natural yogurt bowl", 3.5, 4.7, 3.3, 155, 95, 0.05, 121))
    generated.append(make_item("dairy", "Yogur Griego", "Greek Yogurt", "Griechischer Joghurt", "Yaourt Grec", "Iogurte Grego", "ギリシャヨーグルト", "creamy greek yogurt bowl", 10.0, 3.0, 5.0, 141, 135, 0.04, 110))
    generated.append(make_item("dairy", "Yogur Desnatado", "Low-fat Yogurt", "Fettarmer Joghurt", "Yaourt 0%", "Iogurte Magro", "低脂肪ヨーグルト", "low fat yogurt bowl", 5.3, 7.0, 0.1, 234, 137, 0.07, 183))
    generated.append(make_item("dairy", "Yogur de Fresa", "Strawberry Yogurt", "Erdbeerjoghurt", "Yaourt à la Fraise", "Iogurte de Morango", "イチゴヨーグルト", "strawberry yogurt bowl", 3.0, 15.0, 2.5, 180, 100, 0.05, 110))
    generated.append(make_item("dairy", "Yogur de Vainilla", "Vanilla Yogurt", "Vanillejoghurt", "Yaourt Vanille", "Iogurte de Baunilha", "バニラヨーグルト", "vanilla yogurt bowl", 3.2, 14.0, 2.8, 170, 95, 0.05, 110))
    generated.append(make_item("dairy", "Yogur de Coco", "Coconut Yogurt", "Kokosjoghurt", "Yaourt Coco", "Iogurte de Coco", "ココナッツヨーグルト", "coconut yogurt bowl", 3.0, 12.0, 4.0, 160, 90, 0.05, 100))
    generated.append(make_item("dairy", "Yogur de Soja", "Soy Yogurt", "Sojajoghurt", "Yaourt au Soja", "Iogurte de Soja", "豆乳ヨーグルト", "dairy free soy yogurt bowl", 4.0, 2.0, 2.0, 120, 50, 0.04, 120))
    generated.append(make_item("dairy", "Yogur Sin Lactosa", "Lactose-free Yogurt", "Laktosefreier Joghurt", "Yaourt Sans Lactose", "Iogurte Sem Lactose", "乳糖不使用ヨーグルト", "lactose free yogurt bowl", 3.5, 4.7, 3.3, 155, 95, 0.05, 121))
    generated.append(make_item("dairy", "Yogur de Sabores", "Flavored Yogurt", "Fruchtjoghurt", "Yaourt aux Fruits", "Iogurte de Aromas", "フルーツヨーグルト", "fruit flavored yogurt bowl", 3.0, 15.0, 3.0, 180, 120, 0.1, 130))
    generated.append(make_item("dairy", "Queso Fresco", "Fresh Cheese", "Frischkäse", "Fromage Frais", "Queijo Fresco", "フレッシュチーズ", "fresh white cheese block", 12.0, 3.0, 10.0, 180, 220, 0.5, 550))
    generated.append(make_item("dairy", "Queso Cheddar", "Cheddar", "Cheddar", "Cheddar", "Cheddar", "チェダー", "cheddar cheese block", 25.0, 0.1, 33.0, 98, 512, 1.8, 721))
    generated.append(make_item("dairy", "Queso Parmesano", "Parmesan", "Parmesan", "Parmesan", "Parmesão", "パルメザン", "parmesan cheese wedge", 35.0, 0.0, 29.0, 125, 694, 1.5, 1109))
    generated.append(make_item("dairy", "Queso Mozzarella", "Mozzarella", "Mozzarella", "Mozzarella", "Mozzarella", "モッツァレラ", "fresh mozzarella ball in water", 18.0, 1.0, 17.0, 76, 354, 0.6, 505))
    generated.append(make_item("dairy", "Kefir", "Kefir", "Kefir", "Kéfir", "Kefir", "ケフィア", "glass of kefir drink", 3.0, 4.0, 3.0, 150, 100, 0.04, 120))
    generated.append(make_item("dairy", "Skyr", "Skyr", "Skyr", "Skyr", "Skyr", "スキル", "skyr yogurt bowl", 11.0, 4.0, 0.2, 150, 140, 0.05, 110))
    generated.append(make_item("dairy", "Ayran", "Ayran", "Ayran", "Ayran", "Ayran", "アイラン", "glass of ayran drink", 2.0, 1.5, 1.5, 80, 60, 0.5, 70))
    generated.append(make_item("dairy", "Petit Suisse", "Petit Suisse", "Fruchtzwerge", "Petit Suisse", "Petit Suisse", "プチスイス", "petit suisse yogurt cup", 7.0, 12.0, 3.0, 120, 100, 0.03, 90))
    generated.append(make_item("dairy", "Cuajada", "Curd", "Quark", "Caillé", "Coalhada", "凝乳", "curd dessert bowl", 4.0, 4.0, 5.0, 130, 100, 0.04, 140))
    generated.append(make_item("dairy", "Yogur Líquido", "Drinking Yogurt", "Trinkjoghurt", "Yaourt à Boire", "Iogurte Líquido", "飲むヨーグルト", "drinking yogurt bottle", 3.0, 12.0, 1.5, 140, 90, 0.05, 110))
    
    # Nuts (Special Category: legumes_nuts_group,nuts_spec)
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Nueces", "Walnuts", "Walnüsse", "Noix", "Nozes", "くるみ", "bowl of raw whole walnuts", 15.0, 2.6, 65.0, 441, 346, 0.01, 98))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Almendras", "Almonds", "Mandeln", "Amandes", "Amêndoas", "アーモンド", "bowl of raw almonds with skin", 21.0, 4.0, 49.0, 705, 481, 0.01, 264))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Pistachos", "Pistachios", "Pistazien", "Pistaches", "Pistaches", "ピスタチオ", "bowl of shelled pistachios roasted", 20.0, 7.0, 45.0, 1025, 490, 0.01, 105))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Anacardos", "Cashews", "Cashewkerne", "Noix de cajou", "Caju", "カシューナッツ", "bowl of raw cashews", 18.0, 5.9, 44.0, 660, 593, 0.01, 37))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Avellanas", "Hazelnuts", "Haselnüsse", "Noisettes", "Avelãs", "ヘーゼルナッツ", "bowl of raw hazelnuts", 15.0, 4.0, 60.0, 680, 290, 0.0, 114))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Cacahuetes", "Peanuts", "Erdnüsse", "Cacahuètes", "Amendoins", "ピーナッツ", "bowl of roasted peanuts unsalted", 26.0, 4.0, 49.0, 705, 376, 0.01, 92))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Nueces de Macadamia", "Macadamia", "Macadamia", "Macadamia", "Macadâmia", "マカダミア", "bowl of raw macadamia nuts", 8.0, 4.6, 75.8, 368, 188, 0.01, 85))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Nueces Pecanas", "Pecans", "Pekannüsse", "Noix de Pécan", "Nozes Pecã", "ピーカンナッツ", "bowl of raw pecan nuts", 9.0, 4.0, 72.0, 410, 277, 0.0, 70))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Piñones", "Pine Nuts", "Pinienkerne", "Pignons", "Pinhões", "松の実", "bowl of raw pine nuts", 13.7, 3.7, 68.4, 597, 575, 0.0, 16))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Pipas de Girasol", "Sunflower Seeds", "Sonnenblumenkerne", "Graines de Tournesol", "Sementes de Girassol", "ひまわりの種", "bowl of raw sunflower seeds", 21.0, 2.6, 51.0, 645, 660, 0.01, 78))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Pipas de Calabaza", "Pumpkin Seeds", "Kürbiskerne", "Graines de Citrouille", "Sementes de Abóbora", "かぼちゃの種", "bowl of raw pumpkin seeds", 30.0, 1.0, 49.0, 809, 1233, 0.01, 46))
    generated.append(make_item("legumes_nuts_group,nuts_spec", "Nueces de Brasil", "Brazil Nuts", "Paranüsse", "Noix du Brésil", "Castanha do Pará", "ブラジルナッツ", "bowl of raw brazil nuts", 14.0, 2.3, 67.0, 659, 725, 0.0, 160))
    
    # Fats
    generated.append(make_item("fats", "Aceite de Oliva", "Olive Oil", "Olivenöl", "Huile d'Olive", "Azeite", "オリーブオイル", "olive oil glass bottle", 0.0, 0.0, 100.0, 0, 0, 0.0, 0))
    generated.append(make_item("fats", "Mantequilla", "Butter", "Butter", "Beurre", "Manteiga", "バター", "block of fresh dairy butter", 0.9, 0.1, 81.0, 24, 24, 0.01, 24))
    generated.append(make_item("fats", "Mayonesa", "Mayonnaise", "Mayonnaise", "Mayonnaise", "Maionese", "マヨネーズ", "mayonnaise sauce in a bowl", 1.0, 1.0, 75.0, 20, 28, 0.6, 12))
    
    # Substitutes (Proteins)
    generated.append(make_item("proteins", "Tofu", "Tofu", "Tofu", "Tofu", "Tofu", "豆腐", "fresh white tofu block", 8.0, 0.5, 4.8, 121, 97, 0.01, 350))
    generated.append(make_item("proteins", "Seitán", "Seitan", "Seitan", "Seitan", "Seitan", "セイタン", "seitan wheat gluten pieces", 75.0, 0.0, 1.9, 100, 260, 0.05, 142))
    generated.append(make_item("proteins", "Tempeh", "Tempeh", "Tempeh", "Tempeh", "Tempeh", "テンペ", "fermented tempeh block", 19.0, 0.0, 11.0, 412, 266, 0.01, 111))
    
    # Sweets
    generated.append(make_item("sweets", "Chocolate Negro", "Dark Chocolate", "Dark Chocolate", "Chocolat Noir", "Chocolate Preto", "ダークチョコレート", "dark chocolate pieces", 4.9, 24.0, 42.0, 715, 308, 0.02, 73))
    generated.append(make_item("sweets", "Chocolate con Leche", "Milk Chocolate", "Milchschokolade", "Chocolat au Lait", "Chocolate de Leite", "ミルクチョコレート", "milk chocolate bar", 7.7, 51.0, 29.0, 372, 216, 0.2, 189))
    generated.append(make_item("sweets", "Galletas", "Biscuits", "Kekse", "Biscuits", "Bolachas", "ビスケット", "plate of crispy biscuits", 7.0, 20.0, 12.0, 100, 90, 0.8, 30))
    generated.append(make_item("sweets", "Miel", "Honey", "Honig", "Miel", "Mel", "蜂蜜", "honey jar with dipper", 0.3, 82.0, 0.0, 52, 4, 0.0, 6))
    generated.append(make_item("sweets", "Mermelada", "Jam", "Marmelade", "Confiture", "Compota", "ジャム", "fruit jam jar", 0.5, 60.0, 0.0, 80, 10, 0.0, 15))
    generated.append(make_item("sweets", "Azúcar", "Sugar", "Zucker", "Sucre", "Açúcar", "砂糖", "white sugar cubes bowl", 0.0, 100.0, 0.0, 0, 0, 0.0, 0))
    generated.append(make_item("sweets", "Turrón", "Nougat", "Nougat", "Nougat", "Torrão", "ヌガー", "piece of sweet nougat", 12.0, 45.0, 30.0, 300, 250, 0.05, 60))
    generated.append(make_item("sweets", "Helado", "Ice Cream", "Eiscreme", "Glace", "Gelado", "アイスクリーム", "scoop of vanilla ice cream", 3.5, 21.0, 11.0, 199, 105, 0.08, 128))
    generated.append(make_item("sweets", "Gelatina", "Jelly", "Götterspeise", "Gelée", "Gelatina", "ゼリー", "fruit jelly bowl", 1.2, 14.0, 0.0, 10, 5, 0.02, 3))

    # Drinks
    generated.append(make_item("drinks", "Agua", "Water", "Wasser", "Eau", "Água", "水", "glass of pure mineral water", 0.0, 0.0, 0.0, 0, 0, 0.0, 5))
    generated.append(make_item("drinks", "Infusión de Manzanilla", "Camomile Tea", "Kamillentee", "Camomille", "Camomila", "カモミールティー", "cup of camomile tea", 0.0, 0.0, 0.0, 10, 0, 0.0, 2))
    generated.append(make_item("drinks", "Té", "Tea", "Tee", "Thé", "Chá", "お茶", "cup of hot black tea", 0.0, 0.0, 0.0, 37, 0, 0.0, 0))
    generated.append(make_item("drinks", "Vino Tinto", "Red Wine", "Rotwein", "Vin Rouge", "Vinho Tinto", "赤ワイン", "glass of red wine", 0.2, 0.6, 0.0, 127, 23, 0.01, 8))
    generated.append(make_item("drinks", "Cerveza", "Beer", "Bier", "Bière", "Cerveja", "ビール", "glass of cold beer", 0.5, 3.6, 0.0, 27, 14, 0.01, 4))
    generated.append(make_item("drinks", "Coca Cola", "Cola", "Cola", "Coca", "Coca", "コーラ", "glass of cola soda with ice", 0.0, 10.6, 0.0, 0, 15, 0.01, 2))
    generated.append(make_item("drinks", "Café", "Coffee", "Kaffee", "Café", "Café", "コーヒー", "black coffee cup steaming", 0.1, 0.0, 0.0, 49, 3, 0.0, 2))
    generated.append(make_item("drinks", "Zumo de Naranja", "Orange Juice", "Orangensaft", "Jus d'Orange", "Sumo de Laranja", "オレンジジュース", "fresh orange juice glass", 0.7, 8.4, 0.2, 200, 17, 0.0, 11))
    generated.append(make_item("drinks", "Zumo de Manzana", "Apple Juice", "Apfelsaft", "Jus de Pomme", "Sumo de Maçã", "リンゴジュース", "fresh apple juice glass", 0.1, 9.6, 0.1, 101, 7, 0.0, 5))
    generated.append(make_item("drinks", "Zumo de Piña", "Pineapple Juice", "Ananassaft", "Jus d'Ananas", "Sumo de Abacaxi", "パイナップルジュース", "fresh pineapple juice glass", 0.4, 12.0, 0.1, 130, 8, 0.0, 13))
    generated.append(make_item("drinks", "Zumo de Uva", "Grape Juice", "Traubensaft", "Jus de Raisin", "Sumo de Uva", "ブドウジュース", "glass of purple grape juice", 0.4, 14.0, 0.1, 119, 12, 0.0, 9))
    generated.append(make_item("drinks", "Zumo de Tomate", "Tomato Juice", "Tomatensaft", "Jus de Tomate", "Sumo de Tomate", "トマトジュース", "glass of red tomato juice", 0.8, 2.6, 0.1, 217, 19, 0.05, 8))
    generated.append(make_item("drinks", "Zumo de Pomelo", "Grapefruit Juice", "Grapefruitsaft", "Jus de Pamplemousse", "Sumo de Toranja", "グレープフルーツジュース", "glass of grapefruit juice", 0.5, 9.0, 0.1, 162, 15, 0.0, 9))
    generated.append(make_item("drinks", "Zumo de Zanahoria", "Carrot Juice", "Karottensaft", "Jus de Carotte", "Sumo de Cenoura", "人参ジュース", "glass of carrot juice", 0.9, 3.9, 0.1, 292, 29, 0.04, 24))
    generated.append(make_item("drinks", "Zumo de Melocotón", "Peach Juice", "Pfirsichsaft", "Jus de Pêche", "Sumo de Pêssego", "桃ジュース", "glass of peach juice", 0.4, 8.0, 0.1, 120, 12, 0.0, 5))
    generated.append(make_item("drinks", "Zumo de Pera", "Pear Juice", "Birnensaft", "Jus de Poire", "Sumo de Pêra", "洋梨ジュース", "glass of pear juice", 0.2, 9.0, 0.1, 80, 8, 0.0, 6))
    generated.append(make_item("drinks", "Zumo de Arándanos", "Cranberry Juice", "Cranberrysaft", "Jus de Canneberge", "Sumo de Arando", "クランベリージュース", "glass of cranberry juice", 0.0, 12.0, 0.0, 77, 13, 0.0, 5))
    generated.append(make_item("drinks", "Zumo de Mango", "Mango Juice", "Mangosaft", "Jus de Mangue", "Sumo de Manga", "マンゴージュース", "glass of mango juice", 0.5, 13.0, 0.2, 110, 10, 0.0, 10))
    generated.append(make_item("drinks", "Zumo de Granada", "Pomegranate Juice", "Granatapfelsaft", "Jus de Grenade", "Sumo de Romã", "ザクロジュース", "glass of pomegranate juice", 0.2, 13.0, 0.0, 214, 25, 0.0, 11))
    generated.append(make_item("drinks", "Zumo de Limón", "Lemon Juice", "Zitronensaft", "Jus de Citron", "Sumo de Limão", "レモン汁", "glass of fresh lemon juice", 0.4, 2.5, 0.0, 103, 8, 0.0, 7))
    generated.append(make_item("drinks", "Zumo de Lima", "Lime Juice", "Limettensaft", "Jus de Citron Vert", "Sumo de Lima", "ライム果汁", "glass of fresh lime juice", 0.4, 1.7, 0.0, 117, 10, 0.0, 10))
    generated.append(make_item("drinks", "Zumo Multifruta", "Multifruit Juice", "Multivitaminsaft", "Jus Multifruits", "Sumo Multifrutas", "ミックスジュース", "glass of mixed multifruit juice", 0.5, 11.0, 0.1, 150, 15, 0.0, 10))
    generated.append(make_item("drinks", "Limonada", "Lemonade", "Limonade", "Limonade", "Limonada", "レモネード", "glass of fresh lemonade with ice", 0.1, 10.0, 0.0, 10, 2, 0.0, 2))

    # Snacks (Mixed under carbs/sweets)
    generated.append(make_item("carbs", "Patatas Chips", "Potato Chips", "Kartoffelchips", "Chips de Pomme de Terre", "Batatas Chips", "ポテトチップス", "bowl of crispy potato chips", 6.5, 0.5, 35.0, 1200, 160, 1.5, 25))
    generated.append(make_item("carbs", "Nachos", "Nachos", "Nachos", "Nachos", "Nachos", "ナチョス", "plate of crispy nachos", 7.0, 1.0, 25.0, 250, 180, 1.0, 80))
    generated.append(make_item("carbs", "Palomitas", "Popcorn", "Popcorn", "Pop-corn", "Pipocas", "ポップコーン", "bowl of salted popcorn", 12.0, 0.5, 4.0, 329, 350, 1.0, 10))
    generated.append(make_item("carbs", "Ganchitos", "Cheese Curls", "Käsebällchen", "Soufflés au Fromage", "Ganchitos", "チーズスナック", "bowl of orange cheese curls", 6.0, 2.0, 34.0, 200, 150, 2.0, 50))
    generated.append(make_item("sweets", "Barrita Energética", "Energy Bar", "Energieriegel", "Barre Énergétique", "Barra Energética", "エナジーバー", "oat cereal energy bar", 10.0, 30.0, 15.0, 250, 200, 0.5, 80))
    generated.append(make_item("sweets", "Chocolatina", "Chocolate Bar", "Schokoriegel", "Barre Chocolatee", "Chocolate", "チョコレートバー", "sweet chocolate candy bar", 5.0, 50.0, 30.0, 200, 150, 0.2, 100))
    generated.append(make_item("sweets", "Gominolas", "Gummy Bears", "Gummibärchen", "Gummies", "Gomas", "グミ", "colorful gummy bears bowl", 6.0, 46.0, 0.0, 5, 5, 0.1, 10))
    generated.append(make_item("sweets", "Caramelos", "Hard Candy", "Bonbons", "Bonbons", "Rebuçados", "キャンディ", "colorful wrapped hard candies", 0.0, 98.0, 0.0, 2, 0, 0.05, 5))
    generated.append(make_item("sweets", "Regaliz", "Licorice", "Lakritz", "Réglisse", "Alcaçuz", "リコリス", "black licorice sticks", 3.0, 70.0, 0.5, 100, 50, 0.1, 40))
    generated.append(make_item("carbs", "Pretzels", "Pretzels", "Pretzels", "Bretzels", "Pretzels", "プレッツェル", "salted crispy pretzels", 10.0, 2.0, 5.0, 150, 100, 3.0, 30))
    generated.append(make_item("carbs", "Galletas de Arroz", "Rice Cakes", "Reiswaffeln", "Galettes de Riz", "Bolachas de Arroz", "ポン菓子", "crispy puffed rice cakes", 8.0, 1.0, 3.0, 100, 250, 0.5, 10))

    # Others (Salt, Peppers, Herbs)
    generated.append(make_item("fats", "Sal de Mesa", "Table Salt", "Tafelsalz", "Sel de Table", "Sal de Mesa", "食塩", "pile of white table salt", 0.0, 0.0, 0.0, 0, 0, 100.0, 0))
    generated.append(make_item("drinks", "Vinagre", "Vinegar", "Essig", "Vinaigre", "Vinagre", "酢", "glass bottle of clear vinegar", 0.0, 0.0, 0.0, 2, 2, 0.0, 6))
    generated.append(make_item("fats", "Pimienta Negra", "Black Pepper", "Schwarzer Pfeffer", "Poivre Noir", "Pimenta Preta", "黒胡椒", "ground black pepper powder", 10.0, 0.0, 3.0, 1300, 150, 0.05, 400))
    generated.append(make_item("fats", "Orégano", "Oregano", "Oregano", "Origan", "Orégano", "オレガノ", "dried oregano herb leaves", 9.0, 0.0, 4.0, 1260, 148, 0.05, 1597))
    generated.append(make_item("fats", "Perejil", "Parsley", "Petersilie", "Persil", "Salsa", "パセリ", "fresh green parsley sprigs", 3.0, 0.0, 0.8, 554, 58, 0.05, 138))

    # DB Interaction
    conn = sqlite3.connect('renal_diet.db')
    cursor = conn.cursor()
    
    # 1. Clear existing data (preserving table structure)
    print("Limpiando datos existentes...")
    cursor.execute('DELETE FROM food_nutrients')
    cursor.execute('DELETE FROM food_translations')
    cursor.execute('DELETE FROM foods')
    # Nos aseguramos de resetear los autoincrementales
    cursor.execute('DELETE FROM sqlite_sequence WHERE name IN ("foods", "food_translations", "categories")')
    
    # 2. Asegurar que las categorías existen
    # Extraemos categorías únicas de los datos generados
    unique_categories = set(f["category"] for f in generated)
    for cat_key in unique_categories:
        cursor.execute("INSERT OR IGNORE INTO categories (key) VALUES (?)", (cat_key,))
    
    # Obtener mapeo de categorías
    cursor.execute("SELECT id, key FROM categories")
    category_map = {key: id_ for id_, key in cursor.fetchall()}
    
    # 3. Obtener mapeo de nutrientes
    cursor.execute("SELECT id, key FROM nutrients")
    nutrient_map = {key: id_ for id_, key in cursor.fetchall()}
    
    # 4. Insertar datos
    print(f"Insertando {len(generated)} alimentos...")
    for f in generated:
        # a. Insertar food
        cursor.execute("INSERT INTO foods (category_id, image_url) VALUES (?, ?)", 
                       (category_map[f["category"]], get_image_url(f["image_query"])))
        food_id = cursor.lastrowid
        
        # b. Insertar Traducciones
        translations = [
            ('es', f['name']),
            ('en', f['name_en']),
            ('de', f['name_de']),
            ('fr', f['name_fr']),
            ('pt', f['name_pt']),
            ('ja', f['name_ja'])
        ]
        for lang, name in translations:
            if name:
                cursor.execute("INSERT INTO food_translations (food_id, lang, name) VALUES (?, ?, ?)", 
                               (food_id, lang, name))
        
        # c. Insertar Nutrientes
        nut_values = [
            ('protein', f['protein']),
            ('sugar', f['sugar']),
            ('fat', f['fat']),
            ('potassium', f['potassium']),
            ('phosphorus', f['phosphorus']),
            ('salt', f['salt']),
            ('calcium', f['calcium'])
        ]
        for nut_key, val in nut_values:
            if val is not None:
                cursor.execute("INSERT INTO food_nutrients (food_id, nutrient_id, value) VALUES (?, ?, ?)", 
                               (food_id, nutrient_map[nut_key], val))

    conn.commit()
    print(f"Base de datos actualizada con {len(generated)} items.")
    conn.close()

if __name__ == "__main__":
    populate()
