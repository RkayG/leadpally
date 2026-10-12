 # Map domains to source types
SOURCE_TYPE_MAP = {
    "news": [
        "cnn.com", "bbc.com", "nytimes.com", "reuters.com", "theguardian.com", "washingtonpost.com",
        "forbes.com", "bloomberg.com", "usatoday.com", "wsj.com", "aljazeera.com", "npr.org",
        "apnews.com", "axios.com", "politico.com", "economist.com", "nbcnews.com", "abcnews.go.com",
        "foxnews.com", "cbsnews.com", "cnbc.com", "businessinsider.com", "thehill.com", "huffpost.com",
        "time.com", "newsweek.com", "ft.com", "latimes.com", "chicagotribune.com", "vox.com",
        "slate.com", "thedailybeast.com", "theatlantic.com", "newyorker.com", "independent.co.uk",
        "thetimes.co.uk", "telegraph.co.uk", "dailymail.co.uk", "dw.com", "france24.com",
        "euronews.com", "scmp.com", "japantimes.co.jp", "straitstimes.com", "thehindu.com"
    ],

    "blog": [
        "medium.com", "wordpress.com", "blogspot.com", "substack.com", "tumblr.com", "livejournal.com",
        "dev.to", "hashnode.com", "hashnode.dev", "ghost.io", "wix.com", "squarespace.com", "blogger.com",
        "typepad.com", "weebly.com", "gitlab.io", "github.io", "hubspot.com", "webflow.io",
        "notion.so", "telegraph.co", "beehiiv.com", "mirror.xyz", "revue.co", "patreon.com",
        "svbtle.com", "gumroad.com", "buymeacoffee.com", "ko-fi.com", "podia.com", "teachable.com",
        "contentful.com", "forestry.io", "contentstack.com", "storyblok.com", "contentlayer.dev"
    ],

    "forum": [
        "reddit.com", "quora.com", "stackexchange.com", "stackoverflow.com", "discord.com", "4chan.org",
        "5ch.net", "tapatalk.com", "vbulletin.com", "discourse.org", "lemmy.world", "hackernews.com",
        "ycombinator.com", "slashdot.org", "hn.algolia.com", "xenforo.com", "phpbb.com", "gitter.im",
        "slack.com", "disqus.com", "discoursehosting.net", "flarum.org", "invisioncommunity.com",
        "tribe.so", "vanilla.org", "nodebb.org", "muut.com", "nabble.com", "loomio.org",
        "producthunt.com", "bbpress.org", "forumengine.io", "spectrum.chat", "threadeo.com",
        "circle.so", "sympa.org", "groups.io"
    ],

    "video": [
        "youtube.com", "vimeo.com", "dailymotion.com", "twitch.tv", "metacafe.com", "bitchute.com",
        "veoh.com", "vidyard.com", "rumble.com", "odysee.com", "wistia.com", "brightcove.com", "jwplayer.com", "vdocipher.com",
        "loom.com", "streamable.com", "spotlightr.com", "panopto.com", "kaltura.com", "vzaar.com",
        "uscreen.tv", "kajabi.com", "vhx.tv", "livestream.com", "vzaar.com", "ooyala.com",
        "popcornflix.com", "tubitv.com", "pluto.tv", "crackle.com", "dtube.com", "lbry.tv",
        "peertube.io", "trovo.live", "kick.com", "theta.tv"
    ],

    "social": [
        "facebook.com", "twitter.com", "x.com", "instagram.com", "linkedin.com", "pinterest.com", "snapchat.com",
        "tiktok.com", "reddit.com", "tumblr.com", "quora.com", "discord.com", "whatsapp.com",	
        "telegram.org", "weibo.com", "vk.com", "baidu.com", "wechat.com", "line.me", "kakao.com",
        "skype.com", "signal.org", "slack.com", "flickr.com", "meetup.com"
    ],
    "image": [
        "flickr.com", "imgur.com", "photobucket.com", "tinypic.com", "shutterstock.com",
        "unsplash.com", "pexels.com", "pixabay.com", "stock.adobe.com", "istockphoto.com",
        "gettyimages.com", "depositphotos.com", "dreamstime.com", "canstockphoto.com",
        "bigstockphoto.com", "123rf.com", "fotolia.com", "alamy.com", "stocksy.com",
        "freepik.com", "vecteezy.com", "rawpixel.com", "burst.shopify.com", "reshot.com",
        "rawpixel.com", "canva.com", "crello.com", "snappa.com", "vectr.com", "placeit.net",
        "mockupworld.co", "mockuphone.com", "mockupbro.com", "mockupmark.com", "mockupcloud.com",
        "mockupdesign.com", "mockupzone.com", "mockupart.com", "mockupcloud.co", "mockupworld.co",
       
    ],
    
    "AI": [
        "openai.com", "google.com/ai", "microsoft.com/en-us/research", "ibm.com/watson",
        "amazon.com/aws/machine-learning", "facebook.com/ai", "nvidia.com/en-us/deep-learning-ai",
        "huggingface.co", "deepmind.com", "baidu.com/ai", "tencent.com/en-us/ai",
        "salesforce.com/products/einstein", "oracle.com/artificial-intelligence", "sap.com/products/ai",
        "zoho.com/ai", "hubspot.com/products/ai", "adobe.com/sensei", "c3.ai",
        "palantir.com/solutions/ai", "databricks.com/solutions/ai", "cloudera.com/products/ai",
        "splunk.com/en_us/solutions/ai-ml.html", "servicenow.com/products/ai.html",
        "atlassian.com/software/ai", "slack.com/features/ai", "zoom.us/ai",
    ],
    "sports": [
        "espn.com", "bleacherreport.com", "cbssports.com", "foxsports.com", "nbcsports.com",
        "skysports.com", "goal.com", "fifa.com", "nba.com", "mlb.com", "nfl.com",
        "nhl.com", "pga.com", "tennis.com", "formula1.com", "ufc.com", "si.com", "sportingnews.com",
        "espncricinfo.com", "cricbuzz.com", "rugbyworldcup.com", "olympics.com", "eurosport.com",
        "sbnation.com", "theathletic.com", "deadspin.com", "theringer.com", "fansided.com",
        "yahoo.com/sports", "barstoolsports.com", "fanduel.com", "draftkings.com", "theplayerstribune.com",
        "espnfc.com", "theatlas.com", "bbc.com/sport", "cnn.com/sports", "sportsbusinessjournal.com",
        "golfdigest.com", "soccernet.com", "cyclingnews.com", "uswntplayers.com", "fiba.basketball"
    ],

    
    "ecommerce": [
    "amazon.com", "ebay.com", "etsy.com", "aliexpress.com", "walmart.com", "target.com",
    "flipkart.com", "bestbuy.com", "shopify.com", "rakuten.com", "mercadolibre.com",
    "wayfair.com", "costco.com", "newegg.com", "wish.com", "overstock.com", "homedepot.com",
    "ikea.com", "macys.com", "nordstrom.com", "zappos.com", "asos.com", "jd.com", "taobao.com",
    "alibaba.com", "temu.com", "shein.com", "zalando.com", "lazada.com", "coupang.com",
    "tokopedia.com", "bukalapak.com", "jumia.com", "noon.com", "ozon.ru", "wildberries.ru",
    "trendyol.com", "hepsiburada.com", "cdiscount.com", "allegro.pl", "takealot.com"
    ],

    "education": [
        "coursera.org", "edx.org", "alxafrica.com", "holbertonschool.com", "altschoolafrica.com",
        "udemy.com", "khanacademy.org", "academia.edu", "researchgate.net",
        "mit.edu", "harvard.edu", "stanford.edu", "ox.ac.uk", "cam.ac.uk", "berkeley.edu",
        "yale.edu", "princeton.edu", "caltech.edu", "columbia.edu", "cornell.edu", "upenn.edu",
        "ucla.edu", "nyu.edu", "umich.edu", "ucl.ac.uk", "imperial.ac.uk", "ethz.ch", "tsinghua.edu.cn",
        "jstor.org", "sciencedirect.com", "scholar.google.com", "chegg.com", "brainly.com",
        "brilliant.org", "skillshare.com", "pluralsight.com", "lynda.com", "linkedin.com/learning",
        "masterclass.com", "codecademy.com", "duolingo.com", "quizlet.com", "canvas.net",
        "blackboard.com", "moodle.org", "futurelearn.com", "openlearning.com", "classcentral.com"
    ],

    "technology": [
        "techcrunch.com", "wired.com", "arstechnica.com", "theverge.com", "gizmodo.com", "engadget.com",
        "cnet.com", "zdnet.com", "slashdot.org", "venturebeat.com", "thenextweb.com", "makeuseof.com",
        "tomshardware.com", "anandtech.com", "digitaltrends.com", "androidauthority.com", "9to5mac.com",
        "macrumors.com", "hackernoon.com", "techradar.com", "pcmag.com", "protocol.com", "siliconangle.com",
        "xda-developers.com", "androidpolice.com", "windowscentral.com", "mashable.com", "techrepublic.com",
        "howtogeek.com", "betanews.com", "lifewire.com", "crn.com", "extremetech.com", "ghacks.net",
        "stackoverflow.blog", "infoworld.com", "informationweek.com", "thehackernews.com", "bleepingcomputer.com"
    ],

    "health": [
        "webmd.com", "mayoclinic.org", "healthline.com", "nih.gov", "cdc.gov", "who.int",
        "medlineplus.gov", "clevelandclinic.org", "verywellhealth.com", "everydayhealth.com",
        "drugs.com", "rxlist.com", "medicalnewstoday.com", "health.com", "health.harvard.edu",
        "hopkinsmedicine.org", "cancer.gov", "cancer.org", "heart.org", "diabetes.org",
        "cedars-sinai.org", "kidshealth.org", "psychologytoday.com", "psychiatry.org", "psychiatrist.com",
        "medscape.com", "pubmed.ncbi.nlm.nih.gov", "jamanetwork.com", "nejm.org", "thelancet.com",
        "bmj.com", "nhs.uk", "healthgrades.com", "zocdoc.com", "goodrx.com", "webpagemd.com",
        "menshealth.com", "womenshealth.gov", "myfitnesspal.com", "weightwatchers.com"
    ],

    "finance": [
        "investopedia.com", "marketwatch.com", "bloomberg.com", "forbes.com", "wsj.com", "cnbc.com",
        "seekingalpha.com", "fool.com", "morningstar.com", "bankrate.com", "finance.yahoo.com",
        "ft.com", "barrons.com", "businessinsider.com", "economist.com", "nasdaq.com", "nyse.com",
        "finviz.com", "tradingview.com", "stockcharts.com", "zacks.com", "tipranks.com", "benzinga.com",
        "barchart.com", "marketbeat.com", "nerdwallet.com", "creditkarma.com", "mint.com", "ycharts.com",
        "schwab.com", "tdameritrade.com", "fidelity.com", "vanguard.com", "interactivebrokers.com",
        "etrade.com", "robinhood.com", "wellsfargo.com", "chase.com", "bofa.com", "citibank.com",
        "capitalone.com", "discoverbank.com", "ally.com", "worldbank.org", "imf.org"
    ],

    "entertainment": [
        "imdb.com", "rottentomatoes.com", "metacritic.com", "variety.com", "hollywoodreporter.com",
        "buzzfeed.com", "tmz.com", "etonline.com", "eonline.com", "rollingstone.com",
        "billboard.com", "empireonline.com", "screenrant.com", "cinemablend.com", "deadline.com",
        "vulture.com", "avclub.com", "indiewire.com", "collider.com", "comicbook.com", 
        "comingsoon.net", "fandango.com", "looper.com", "movieweb.com", "tvguide.com",
        "tvline.com", "justjared.com", "perezhilton.com", "popsugar.com", "complex.com",
        "pitchfork.com", "stereogum.com", "spin.com", "consequence.net", "loudwire.com",
        "nme.com", "thefader.com", "digitalspy.com", "popculture.com", "screencrush.com"
    ],

    "government": [
        "usa.gov", "gov.uk", "europa.eu", "nasa.gov", "whitehouse.gov", "senate.gov", "house.gov",
        "un.org", "state.gov", "justice.gov", "treasury.gov", "defense.gov", "energy.gov", "hhs.gov",
        "dhs.gov", "ed.gov", "fda.gov", "epa.gov", "fbi.gov", "cia.gov", "nsa.gov", "usaid.gov",
        "usps.com", "ssa.gov", "irs.gov", "cms.gov", "va.gov", "loc.gov", "noaa.gov", "usda.gov",
        "census.gov", "ftc.gov", "fcc.gov", "sec.gov", "uspto.gov", "gsa.gov", "sba.gov", "federalreserve.gov",
        "supremecourt.gov", "dol.gov", "doi.gov", "dot.gov", "commerce.gov", "hud.gov", "nrc.gov"
    ],

    "shopping": [
        "shopify.com", "bigcommerce.com", "woocommerce.com", "magento.com", "prestashop.com",
        "opencart.com", "squarespace.com", "wix.com", "weebly.com", "volusion.com", "3dcart.com",
        "ecwid.com", "lightspeedhq.com", "shift4shop.com", "salesforce.com/commerce-cloud", "cs-cart.com",
        "oscommerce.com", "zencart.com", "nopcommerce.com", "virtuemart.net", "demandware.com",
        "shopatron.com", "sap.com/products/commerce-cloud", "oracle.com/commerce", "ibm.com/products/websphere-commerce",
        "mycommerce.com", "marketpress.com", "jigoshop.com", "drupalcommerce.org", "ubercart.org",
        "deskera.com", "ecommerceplatforms.com", "pinnacle-cart.com", "storehippo.com", "shopline.com"
    ],

    "travel": [
        "tripadvisor.com", "expedia.com", "booking.com", "airbnb.com", "kayak.com", "skyscanner.net",
        "lonelyplanet.com", "travelocity.com", "agoda.com", "hotels.com", "vrbo.com", "orbitz.com",
        "priceline.com", "hotwire.com", "trivago.com", "hopper.com", "hostelworld.com", "viator.com",
        "fodors.com", "frommers.com", "ricksteves.com", "cruisecritic.com", "wanderlog.com", "roadtrippers.com",
        "rome2rio.com", "seatguru.com", "flightaware.com", "flightradar24.com", "airdna.co", "homeaway.com",
        "couchsurfing.com", "thrillophilia.com", "getyourguide.com", "klook.com", "flixbus.com",
        "trainline.com", "amtrak.com", "nationalrail.co.uk", "rentalcars.com", "uber.com",
        "lyft.com", "rome2rio.com", "passrider.com", "seatguru.com", "afar.com"
    ],
    "food": [
        "zomato.com", "grubhub.com", "ubereats.com", "doordash.com",
        "postmates.com", "seamless.com", "deliveroo.co.uk", "just-eat.co.uk", "swiggy.com", 
        "dominos.com", "pizzahut.com", "subway.com", "starbucks.com", "dunkindonuts.com",
        "panerabread.com", "chipotle.com", "tacobell.com", "burgerking.com", "wendys.com",
        "kfc.com", "mcdonalds.com", "fiveguys.com", "chick-fil-a.com", "pandaexpress.com",
        "olivegarden.com", "redlobster.com", "cheesecakefactory.com", "ihop.com",
        "dennys.com", "wafflehouse.com", "crackerbarrel.com", "buffalowildwings.com", "applebees.com",
        "chilis.com", "tgi-fridays.com", "redrobin.com", "carrabbas.com", "bonefishgrill.com",
        "longhornsteakhouse.com", "texasroadhouse.com", "fogo.com", "sizzler.com", "outback.com",
        "steakhouse.com", "benihana.com", "hibachigrill.com", "sushihouse.com", "sushiking.com",
        "sushisamba.com", "sushiro.com", "sushimania.com", "sushitown.com", "sushiholic.com",
    ],

    "real_estate": [
        "zillow.com", "realtor.com", "trulia.com", "redfin.com", "apartments.com", "homes.com",
        "loopnet.com", "crexi.com", "propertyshark.com", "movoto.com", "realtytrac.com",
        "homefinder.com", "rent.com", "hotpads.com", "forrent.com", "rentalhomesplus.com",
        "landwatch.com", "landandfarm.com", "remax.com", "century21.com", "coldwellbanker.com",
        "kw.com", "sothebysrealty.com", "bhgre.com", "expworldholdings.com"
    ],
    "automotive": [
        "autotrader.com", "cars.com", "carmax.com", "kbb.com", "edmunds.com", "truecar.com",
        "carvana.com", "vroom.com", "motortrend.com", "jalopnik.com", "roadandtrack.com",
        "caranddriver.com", "autoblog.com", "topgearmagazine.com", "driving.ca", "autoweek.com",
        "thecarconnection.com", "automobilemag.com", "hagerty.com", "classiccars.com",
        "bringatrailer.com", "carsguide.com.au", "drive.com.au", "caradvice.com.au",
        "carsales.com.au"
    ],
    "music": [
        "spotify.com", "apple.com/music", "soundcloud.com", "bandcamp.com", "tidal.com",
        "deezer.com", "pandora.com", "last.fm", "8tracks.com", "mixcloud.com",
        "hearthis.at", "jamendo.com", "reverbnation.com", "datpiff.com", "audiomack.com",
        "hype machine.com", "music.apple.com", "genius.com", "musixmatch.com", 
        "shazam.com", "songkick.com"
    ],
    "podcast": [
        "apple.com/podcasts", "spotify.com/podcasts", "stitcher.com", "podbean.com", "tunein.com",
        "overcast.fm", "castbox.fm", "pocketcasts.com", "audioboom.com", "podchaser.com",
        "podnews.net", "radiopublic.com", "luminarypodcasts.com", "castro.fm", "breaker.audio",
        "simplecast.com", "libsyn.com", "buzzsprout.com", "transistor.fm", "redcircle.com",
        "podomatic.com"
    ],
    "fashion": [
        "vogue.com", "elle.com", "harpersbazaar.com", "gq.com", "fashionista.com", "refinery29.com",
        "whowhatwear.com", "manrepeller.com", "thezoereport.com", "stylecaster.com", "popfashion.com",
        "fashionbeans.com", "hypebeast.com", "highsnobiety.com", "complex.com/style",
        "streetwearnews.com", "sneakernews.com", "footwearnews.com", "fashionnova.com",
        "asos.com", "zara.com", "hm.com", "forever21.com", "urbanoutfitters.com"
    ],
    "lifestyle": [
        "buzzfeed.com/lifestyle", "lifehacker.com", "apartmenttherapy.com", "thekitchn.com",
        "mindbodygreen.com", "thespruce.com", "goodhousekeeping.com", "realhomes.com",
        "countryliving.com", "betterhomesandgardens.com", "marthastewart.com", "hgtv.com",
        "thisoldhouse.com", "diynetwork.com", "familyhandyman.com", "bobvila.com",
        "thepioneerwoman.com", "foodnetwork.com", "allrecipes.com", "epicurious.com",
        "yummly.com"
    ],
    "parenting": [
        "babycenter.com", "whattoexpect.com", "parents.com", "momjunction.com", "thebump.com",
        "verywellfamily.com", "scarymommy.com", "mommynearest.com", "fatherly.com",
        "daddybloggers.com", "mommybloggers.com", "parenting.com",
        "mommyshorts.com",  "mommyish.com", 
    ],
    "pets": [
        "petmd.com", "akc.org", "thebark.com", "petsmart.com", "petco.com", "chewy.com",
        "adoptapet.com", "bestfriends.org", "dogster.com",
        "catster.com", "vetstreet.com", "animalplanet.com", "peta.org", "aspca.org",
        "humane society.org", "petrescue.com", "pawboost.com", "lostmypet.com"
    ],
    
    "gaming": [
        "ign.com", "gamespot.com", "kotaku.com", "polygon.com", "pcgamer.com", "rockpapershotgun.com",
        "gameinformer.com", "destructoid.com", "n4g.com", "metacritic.com/games", "steamunlocked.net",
        "epicgames.com/store/en-US/", "gog.com", "itch.io", "humblebundle.com", "origin.com",
        "battle.net", "uplay.com", "xbox.com/en-US/games", "playstation.com/en-us/games",
        "nintendo.com/games/", "gamefaqs.gamespot.com", "neogaf.com", "resetera.com",
        "reddit.com/r/gaming"
    ],
        
    "crypto": [
        "coinbase.com", "binance.com", "kraken.com", "coinmarketcap.com", "coingecko.com", 
        "blockchain.com", "crypto.com", "ethereum.org", "bitcoin.org", "cardano.org",
        "polkadot.network", "solana.com", "uniswap.org", "opensea.io", "metamask.io",
        "chainlink.com", "ftx.com", "bitfinex.com", "gemini.com", "kucoin.com", 
        "bybit.com", "huobi.com", "okx.com", "gate.io", "pancakeswap.finance",
        "sushi.com", "aave.com", "compound.finance", "makerdao.com", "curve.fi",
        "yearn.finance", "synthetix.io", "avalabs.org", "dogecoin.com", "shiba.info",
        "serum-dex.com", "ftmscan.com", "arbitrum.io", "optimism.io", 
        "nexo.io", "celsius.network", "blockfi.com", "ledger.com", "trezor.io", 
        "cointelegraph.com", "coindesk.com", "decrypt.co", "theblockcrypto.com", "cryptoslate.com"
    ]

}
