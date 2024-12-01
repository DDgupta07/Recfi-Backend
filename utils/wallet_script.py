from trade.models import Recifi


wallets = [
    ("0xebf0b4aa890098cd3e551e4a4c4f3a9bd01f3025", "Peyote"),
    ("0x107b45fd7cd861bfd206312ce2384dafbb2ab083", "Chai Honey"),
    ("0x93764f433f1eff622f9b7649272e14c5780a929d", "Ishzan"),
    ("0xa87c0440d7568d85321fb06f59bdc1c0745e8248", "Whale Fud"),
    ("0x9badae7a4a9030d094b799f13b306d2f462f9be9", "Erik Strevens"),
    ("0x7cb9eaf6c0ca9596f92d3c120eb008e805249bab", "CGJ"),
    ("0xd4aef64c6332b785ce3bd5192ce1e72543027281", "CRG"),
    ("0x55D8121b99e976fD0EEfc595B4a51975fD1537b7", "spurdo dev"),
    ("0x7e6b92f18FB7f7Bd1deFE0B109cF93086c2D02f3", "Sniper i copy"),
    ("0xCB5197Bb7319acBd3C7351B25d94f80999EB81CA", "copy trader"),
    ("0xCF2Ee86dAaE7e364c7C05643E815C8D2498e2466", "$nft $porkfork insider"),
    ("0x250d1bfaBC3A4c1578A492C27cF8d6695fc51098", "nuker insider 2"),
    ("0xcDA31b98131B059FE6464963F1F474De6e13eB2b", "nuker insider 3"),
    ("0xb6380198D5D96D9a950714f9eFF9EBF283307180", "nukes insider 4"),
    ("0x7ce9dA83253aFA7677c18815747a1adB271F92cA", "nuked insider 5"),
    ("0x920668E3a6f6b87948d16954068F631221A65DC0", "peyote side wallet"),
    ("0x3216C586B6E682Fc5cd41ddc2abEf6A0C71d22C3", "GCR Trump wallet"),
    ("0xf8Ce9f1bD06C7559ff45336D55B1C9de46CE019D", "Waxi big trump wallet"),
    ("0x96357756598B5e034aea83e9163bF5C6FD5f66Ec", "Risitas whales NPC"),
    ("0x90B298f5fF8A52D15C2709087f327Af698Fe9729", "Pyrexpyrex"),
    ("0xfc78CC152704c3C8c648fF17842fe80611e676D2", "Baio whale"),
    ("0x50a21cdf9B967Bd11e0ECc39da338F1e44f073Bb", "Lockin"),
    ("0x50664edE715e131F584D3E7EaAbd7818Bb20A068", "Yfimaxi"),
    ("0xaE549B969Dc91b022B8CF1Ef2d5d5D2131aC00F7", "Cryptonut"),
    ("0x19BB9296A7a093C3A78F6F435E42F75C4E5248Ef", "Nois7"),
    ("0x7431931094e8BAe1ECAA7D0b57d2284e121F760e", "TomJ"),
    ("0x17D359c569e63877a215690b557Ded877aA12bE3", "Bananamaximilist"),
    ("0xD57B086DF589055E8d11a5fe5460Dc358F128f2c", "Bond of crypto"),
    ("0x7441934c930C532a6833BE8Fdd9d3f8207E01460", "Banana insider"),
    ("0xf92897b9A7FfCfE18bcE4Ca9ED31b45ad25c2808", "Banana insider"),
]


def add_Recifi_wallets():
    for wallet_address, name in wallets:
        Recifi.objects.create(name=name, wallet_address=wallet_address)
