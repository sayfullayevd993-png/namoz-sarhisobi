"""
O'zbekiston viloyatlari va tuman/shaharlari ro'yxati.
namoz-vaqti.uz API sluglari bilan muvofiqlashtirilgan.
"""

REGIONS_DATA = {
    "toshkent_sh": {
        "name": "Toshkent shahri",
        "districts": [
            {"name": "Toshkent shahri (Umumiy)", "slug": "toshkent-shahri"},
            {"name": "Olmazor tumani", "slug": "olmazor"},
            {"name": "Chilonzor tumani", "slug": "chilonzor"},
            {"name": "Shayxontohur tumani", "slug": "shayxontohur"},
            {"name": "Yunusobod tumani", "slug": "yunusobod"},
            {"name": "Uchtepa tumani", "slug": "uchtepa"},
            {"name": "Mirzo Ulug'bek tumani", "slug": "mirzo-ulugbek"},
            {"name": "Mirobod tumani", "slug": "mirobod"},
            {"name": "Yakkasaroy tumani", "slug": "yakkasaroy"},
            {"name": "Yashnobod tumani", "slug": "yashnobod"},
            {"name": "Sergeli tumani", "slug": "sergeli"},
            {"name": "Bektemir tumani", "slug": "bektemir"},
            {"name": "Yangihayot tumani", "slug": "yangihayot"},
        ]
    },
    "toshkent_vil": {
        "name": "Toshkent viloyati",
        "districts": [
            {"name": "Nurafshon shahri", "slug": "nurafshon"},
            {"name": "Angren shahri", "slug": "angren"},
            {"name": "Olmaliq shahri", "slug": "olmaliq"},
            {"name": "Chirchiq shahri", "slug": "chirchiq"},
            {"name": "Bekobod shahri", "slug": "bekobod"},
            {"name": "Yangiyo'l shahri", "slug": "yangiyol"},
            {"name": "G'azalkent (Bo'stonliq)", "slug": "gazalkent"},
            {"name": "Parkent tumani", "slug": "parkent"},
            {"name": "Piskent tumani", "slug": "piskent"},
            {"name": "Oqqo'rg'on tumani", "slug": "oqqorgon"},
            {"name": "Qibray tumani", "slug": "qibray"},
            {"name": "Zangiota tumani", "slug": "zangiota"},
            {"name": "Chinoz tumani", "slug": "chinoz"},
        ]
    },
    "samarqand": {
        "name": "Samarqand viloyati",
        "districts": [
            {"name": "Samarqand shahri", "slug": "samarqand-shahri"},
            {"name": "Kattaqo'rg'on shahri", "slug": "kattaqorgon"},
            {"name": "Urgut tumani", "slug": "urgut"},
            {"name": "Bulung'ur tumani", "slug": "bulungur"},
            {"name": "Jomboy tumani", "slug": "jomboy"},
            {"name": "Ishtixon tumani", "slug": "ishtixon"},
            {"name": "Oqdaryo tumani", "slug": "oqdaryo"},
            {"name": "Pastdarg'om tumani", "slug": "pastdargom"},
            {"name": "Payariq tumani", "slug": "payariq"},
            {"name": "Narpay tumani", "slug": "narpay"},
            {"name": "Toyloq tumani", "slug": "toyloq"},
        ]
    },
    "fargona": {
        "name": "Farg'ona viloyati",
        "districts": [
            {"name": "Farg'ona shahri", "slug": "fargona-shahri"},
            {"name": "Qo'qon shahri", "slug": "qoqon"},
            {"name": "Marg'ilon shahri", "slug": "margilon"},
            {"name": "Quva tumani", "slug": "quva"},
            {"name": "Rishton tumani", "slug": "rishton"},
            {"name": "Oltiariq tumani", "slug": "oltiariq"},
            {"name": "Beshariq tumani", "slug": "beshariq"},
            {"name": "Yaypan shahri", "slug": "yaypan"},
            {"name": "So'x tumani", "slug": "sox"},
        ]
    },
    "andijon": {
        "name": "Andijon viloyati",
        "districts": [
            {"name": "Andijon shahri", "slug": "andijon-shahri"},
            {"name": "Asaka shahri", "slug": "asaka"},
            {"name": "Shahrixon shahri", "slug": "shahrixon"},
            {"name": "Xonobod shahri", "slug": "xonobod"},
            {"name": "Bo'z (Bo'ston) tumani", "slug": "boz"},
            {"name": "Qo'rg'ontepa tumani", "slug": "qorgontepa"},
            {"name": "Paxtaobod tumani", "slug": "paxtaobod"},
            {"name": "Marhamat tumani", "slug": "marhamat"},
            {"name": "Oltinko'l tumani", "slug": "oltinkol"},
        ]
    },
    "namangan": {
        "name": "Namangan viloyati",
        "districts": [
            {"name": "Namangan shahri", "slug": "namangan-shahri"},
            {"name": "Chust shahri", "slug": "chust"},
            {"name": "Pop shahri", "slug": "pop"},
            {"name": "Kosonsoy shahri", "slug": "kosonsoy"},
            {"name": "To'raqo'rg'on tumani", "slug": "toraqorgon"},
            {"name": "Uchqo'rg'on shahri", "slug": "uchqorgon"},
            {"name": "Chortoq shahri", "slug": "chortoq"},
            {"name": "Mingbuloq tumani", "slug": "mingbuloq"},
        ]
    },
    "buxoro": {
        "name": "Buxoro viloyati",
        "districts": [
            {"name": "Buxoro shahri", "slug": "buxoro-shahri"},
            {"name": "G'ijduvon tumani", "slug": "gijduvon"},
            {"name": "Kogon shahri", "slug": "kogon"},
            {"name": "Vobkent tumani", "slug": "vobkent"},
            {"name": "Qorako'l tumani", "slug": "qorakol"},
            {"name": "Olot tumani", "slug": "olot"},
            {"name": "Shofirkon tumani", "slug": "shofirkon"},
            {"name": "Romitan tumani", "slug": "romitan"},
            {"name": "Jondor tumani", "slug": "jondor"},
        ]
    },
    "qashqadaryo": {
        "name": "Qashqadaryo viloyati",
        "districts": [
            {"name": "Qarshi shahri", "slug": "qarshi"},
            {"name": "Shahrisabz shahri", "slug": "shahrisabz"},
            {"name": "Koson tumani", "slug": "koson"},
            {"name": "Kitob tumani", "slug": "kitob"},
            {"name": "G'uzor tumani", "slug": "guzor"},
            {"name": "Dehqonobod tumani", "slug": "dehqonobod"},
            {"name": "Muborak tumani", "slug": "muborak"},
            {"name": "Yakkabog' tumani", "slug": "yakkabog"},
            {"name": "Qamashi tumani", "slug": "qamashi"},
        ]
    },
    "surxondaryo": {
        "name": "Surxondaryo viloyati",
        "districts": [
            {"name": "Termiz shahri", "slug": "termiz"},
            {"name": "Denov shahri", "slug": "denov"},
            {"name": "Sherobod tumani", "slug": "sherobod"},
            {"name": "Boysun tumani", "slug": "boysun"},
            {"name": "Sho'rchi tumani", "slug": "shorchi"},
            {"name": "Qumqo'rg'on tumani", "slug": "qumqorgon"},
            {"name": "Jarqo'rg'on tumani", "slug": "jarqorgon"},
            {"name": "Sariosiyo tumani", "slug": "sariosiyo"},
            {"name": "Uzun tumani", "slug": "uzun"},
        ]
    },
    "xorazm": {
        "name": "Xorazm viloyati",
        "districts": [
            {"name": "Urganch shahri", "slug": "urganch"},
            {"name": "Xiva shahri", "slug": "xiva"},
            {"name": "Xonqa tumani", "slug": "xonqa"},
            {"name": "Hazorasp tumani", "slug": "hazorasp"},
            {"name": "Gurlan tumani", "slug": "gurlan"},
            {"name": "Shovot tumani", "slug": "shovot"},
            {"name": "Bog'ot tumani", "slug": "bogot"},
            {"name": "Qo'shko'pir tumani", "slug": "qoshkopir"},
        ]
    },
    "navoiy": {
        "name": "Navoiy viloyati",
        "districts": [
            {"name": "Navoiy shahri", "slug": "navoiy"},
            {"name": "Zarafshon shahri", "slug": "zarafshon"},
            {"name": "Karmana tumani", "slug": "karmana"},
            {"name": "Qiziltepa tumani", "slug": "qiziltepa"},
            {"name": "Nurota tumani", "slug": "nurota"},
            {"name": "Konimex tumani", "slug": "konimex"},
            {"name": "Uchquduq shahri", "slug": "uchquduq"},
            {"name": "Xatirchi tumani", "slug": "xatirchi"},
        ]
    },
    "jizzax": {
        "name": "Jizzax viloyati",
        "districts": [
            {"name": "Jizzax shahri", "slug": "jizzax-shahri"},
            {"name": "Zomin tumani", "slug": "zomin"},
            {"name": "G'allaorol tumani", "slug": "gallaorol"},
            {"name": "Paxtakor tumani", "slug": "paxtakor"},
            {"name": "Do'stlik tumani", "slug": "dostlik"},
            {"name": "Baxmal tumani", "slug": "baxmal"},
            {"name": "Zarbdor tumani", "slug": "zarbdor"},
            {"name": "Forish tumani", "slug": "forish"},
        ]
    },
    "sirdaryo": {
        "name": "Sirdaryo viloyati",
        "districts": [
            {"name": "Guliston shahri", "slug": "guliston-shahri"},
            {"name": "Shirin shahri", "slug": "shirin"},
            {"name": "Yangiyer shahri", "slug": "yangiyer"},
            {"name": "Boyovut tumani", "slug": "boyovut"},
            {"name": "Sirdaryo tumani", "slug": "sirdaryo"},
            {"name": "Sayxunobod tumani", "slug": "sayxunobod"},
            {"name": "Oqoltin tumani", "slug": "oqoltin"},
            {"name": "Sardoba tumani", "slug": "sardoba"},
        ]
    },
    "qoraqalpogiston": {
        "name": "Qoraqalpog'iston Respublikasi",
        "districts": [
            {"name": "Nukus shahri", "slug": "nukus"},
            {"name": "Beruniy shahri", "slug": "beruniy"},
            {"name": "To'rtko'l shahri", "slug": "tortkol"},
            {"name": "Xo'jayli shahri", "slug": "xojayli"},
            {"name": "Chimboy tumani", "slug": "chimboy"},
            {"name": "Qo'ng'irot tumani", "slug": "qongirot"},
            {"name": "Mo'ynoq tumani", "slug": "moynoq"},
            {"name": "Taxtako'pir tumani", "slug": "taxtakopir"},
            {"name": "Mang'it shahri", "slug": "mangit"},
        ]
    }
}

def get_region_name_by_key(region_key: str) -> str:
    region = REGIONS_DATA.get(region_key)
    return region["name"] if region else ""

def find_district_by_slug(slug: str):
    for r_key, r_info in REGIONS_DATA.items():
        for d in r_info["districts"]:
            if d["slug"] == slug:
                return {
                    "region_key": r_key,
                    "region_name": r_info["name"],
                    "district_name": d["name"],
                    "slug": d["slug"]
                }
    return None
