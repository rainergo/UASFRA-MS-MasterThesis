# Section: params for re_pattern
hyphen_chars: str = '-*'  # Note: The chars therein must be present in function: RE_BULLET_POINTS.sub(repl="*", string=text)
repeat_chars: str = "-_,.:!?/*"  # Note: Duplicate chars of these get deduplicated
www_domains: list = ['com', 'de', 'net', 'org', 'io', 'co', 'us', 'uk', 'au', 'edu', 'int', 'gov', 'ai', 'biz']
sentence_end_chars: list = [".", ":", "!", "?"]
required_seperator_at_last_position_of_geo_pattern: str = r'[.:!?-]'
company_name_bindings: list[str] = ['-', '&', '+', 'and', 'und', 'y', 'et', "'"]
company_name_articles: list[str] = ['les', 'le', 'de', 'des', 'du', 'del', "l'", 'la', 'mon', 'the', 'der', 'die', 'das']


# Section: Other params
abbreviations: list[str] = [
    'a.o.', 'a.rh.', 'amtl.', 'anh.', 'ank.', 'anl.', 'anm.', 'anschl.', 'app.', 'art.',
    'aufl.',
    'ausg.', 'b.w.', 'bd.', 'bde.', 'beil.', 'bes.', 'betr.', 'bev.', 'bez.', 'bhf.', 'brit.',
    'bspw.', 'bzgl.', 'bzw.', 'chr.', 'corp.', 'd.h.', 'd.i.', 'd.j.', 'd.m.', 'd.o.', 'd.ae.',
    'dazw.', 'de.', 'de.mem', 'desgl.', 'dgl.', 'dipl.', 'dir.', 'dr.', 'dt.', 'dtzd.', 'e.h.',
    'e.v.', 'e.wz.', 'ehem.', 'eigtl.', 'einschl.', 'engl.', 'entspr.', 'erb.', 'erw.', 'ev.',
    'evtl.', 'exkl..', 'fa.', 'fam.', 'ffm.', 'fr.', 'frfr.', 'frl.', 'frz.', 'geb.', 'gebr.',
    'gedr.', 'gegr.', 'gek.', 'ges.', 'gesch.', 'geschl.', 'geschr.', 'gest.', 'gez.', 'ggf.',
    'ggfs.', 'hpts.', 'hptst.', 'hr.', 'hrn.', 'hrsg.', 'i.a.', 'i.b.', 'i.d.', 'i.h.', 'i.j.',
    'i.r.', 'i.v.', 'ing.', 'inh.', 'inkl.', 'inzw.', 'jew.', 'jh.', 'jhrl.', 'k.a.', 'kath.',
    'kfm.', 'kl.', 'kompl.', 'led.', 'ltd.', 'm.a.w.', 'm.e.', 'm.m.', 'm.m.n.', 'm.w.', 'm.ue.m.',
    'mdl.', 'mil.', 'mill.', 'mio.', 'mrd.', 'msp.', 'mtl.', 'moebl.', 'n.j.', 'norw.', 'nr.',
    'naeml.', 'noerdl.', 'o.a.', 'o.b.', 'o.g.', 'o.ae.', 'od.', 'pfd.', 'pkt.', 'pl.', 's.a.',
    's.o.',
    's.u.', 'sa.', 'sek.', 'sog.', 'st.', 'std.', 'str.', 'tel.', 'taegl.', 'u.a.', 'u.a.m.', 'u.u.',
    'u.v.a.', 'u.zw.', 'u.ae.', 'usw.', 'v.a.', 'v.h.', 'v.t.', 'vgl.', 'vj.', 'w.o.', 'wstl.',
    'z.t.', 'z.z.', 'z.zt.', 'ztr.', 'zus.', 'zzgl.', 'uebl.', 'ueblw.']

abbrevs_lengths: list[str] = ['mm', 'cm', 'm', 'km']
abbrevs_numerals: list[str] = ['mil.', 'mill.', 'mio.', 'mrd.', 'tsd.']
abbrevs_titles: list[str] = ['b.a.', 'b.s.', 'c.p.a.', 'cfa', 'dr.', 'j.d.', 'm.a.', 'm.d.', 'm.s.', 'ph.d.', 'prof.']

# Note: Add both versions, with and without period ('.') if such versions are found commonly
company_suffixes_legal_form: list[str] = ['& Cie SA', 'a.s.', 'a/s', 'ag', 'ag & co.', 'ag & co. kgaa',
                                          'aktiengesellschaft', 'american depositary shares', 'aps', 'as', 'asa',
                                          'associates', 'ay', 'b.v.', 'bf', 'bv', 'ciegbr', 'co', 'co.',
                                          'common stockcorp', 'corp.', 'corporation',
                                            'cv', 'gmbh', 'gmbh & co.', 'gmbh & co. kgaa',
                                          'gmbh & co. kommanditgesellschaft auf aktien',
                                          'gruppe', 'group', 'groupe',
                                           'holdings', 'holding', '(holding)', 'schiffsholding',
                                          'inc.', 'k.s.', 'kg', 'kgaa', 'corporate', 'beteiligungsholding', 'consolidated', 'offshore', 'franchise',
                                          'kia', 'kommanditgesellschaft auf aktien', 'limited', 'llp', 'ltd', 'ltd.',
                                          'n.v.', 'nv', 'oy', 'p.l.c.', 'partnership', 'plc', 'plc.',
                                          'public limited company', 'reit', 's.a.', 's.a.e.', 's.a.s.', 's.b.', 's.e.',
                                          's.p.a', 's.p.a.', 's.r.o.', 'sa', 'sapa', 'sarl', 'sas', 'sasu', 'sc', 'sca',
                                          'scs', 'se', 'se & co. kgaa', 'sia', 'sl', 'snc', 'societa benefit',
                                          'societa per azioni', 'societa per azioni s.b.', 'societe anonyme',
                                          'societe cooperative', 'societe en commandite par actions',
                                          'societe europeenne', 'societe fermiere', 'socimi', 'sp. z o.o.', 'spa',
                                          'srl', 'stiftung & Co. kgaa', 'stiftung & co. kgaa', 'ull', 'vof']

# Note: Locations should later be read from countries.csv and cities.csv
geographic_expressions: list = ['africa', 'alpes', 'american', 'baden-wuerttemberg', 'caledonia', 'clairefontaine',
                                'deutsche', 'deutschland', 'eastern', 'egypt', 'francaise', 'france', 'grenobloise',
                                'heidelberg', 'heidelberger', 'hollywood', 'kea', 'loire', 'madagascar', 'mainz', 'marseillaise',
                                'mauna', 'mont-blanc', 'netherlands', 'nice', 'northern', 'nuernberger', 'occidente',
                                'oxford', 'paris', 'rathauseck', 'royan', 'santander', 'schweizer', 'scottish',
                                'southern', 'uk', 'unterhaching', 'val', 'western', 'ithaca']

common_person_names_in_company_names: list = ['barbara', 'bastei', 'bauer', 'beck', 'bijou', 'bloomsbury', 'bogart', 'brigitte',
                                              'brockhaus', 'butlers', 'eiffel', 'feldmeier', 'friedrich', 'halstead', 'hill', 'hilton',
                                              'hoffmann', 'jacques', 'james', 'jean', 'johnson', 'knaus', 'koenig', 'lang', 'lebon',
                                              'ludwig', 'luebbe', 'marley', 'marshall', 'mitchell', 'morgan', 'mueller',
                                              'muenchmeyer', 'nicholson', 'petersen', 'russ', 'schwarz', 'sindall', 'smith',
                                              'tabbert', 'utz', 'uzin', 'fuller', 'turner']

company_suffixes_industry_hints: list[str] = [
    # Note: Only make them optional after the 2nd word (because of i.e. Anglo American)
    'acquisition', 'acquisitions', 'advertising', 'advice', 'advisory', 'aero', 'aeroport', 'agricultural', 'agripower', 'ai',
    'airlines', 'analytics', 'apotheke', 'arbitrage', 'architekt', 'architect', 'aseguradora', 'asset', 'assets', 'auction', 'automobil', 'auto', 'automoción',
    'automotive', 'aviation', 'banca', 'banco', 'bank', 'banking', 'banksysteme', 'beauty', 'bergbau', 'bet', 'beteiligungen',
    'beteiligungs', 'betting', 'bioenergies', 'biogas', 'biolabs', 'biologics', 'biomed', 'biosafety', 'bioscience',
    'biosciences', 'biotech', 'biotechnology', 'bitcoin', 'blockchain', 'bourse', 'boerse', 'brewery', 'building',
    'buildings', 'capital', 'carbon', 'care', 'casino', 'catering', 'celulosa', 'cement', 'chemie', 'cleantech',
    'clinic', 'communication', 'communications', 'construcciones', 'constructeurs', 'consulting', 'consultores',
    'contratas', 'copper', 'cosmetic', 'credit', 'crypto', 'cybersecurity', 'defence', 'delivery', 'design',
    'diagnostics', 'diamonds', 'digital', 'diploma', 'distribution', 'distributions', 'drilling', 'drinks', 'drone',
    'eat',
    'eateries', 'eaux', 'effecten', 'electric', 'electrical', 'electricite', 'electronic', 'electronics',
    'electronique', 'elektronik', 'elektronische', 'energie', 'energy', 'energía', 'engineering', 'engines',
    'entertainment', 'environment', 'environmental', 'environnement', 'equipment', 'esports', 'estate', 'events',
    'exchange', 'exploration', 'familienversicherung', 'farm', 'farma', 'fashion', 'fiducial', 'finance', 'finances',
    'financial', 'financiere', 'financiero', 'fintec', 'fonciere', 'food', 'foods', 'football', 'forestry', 'forfait',
    'fotovoltaico', 'fund', 'funding', 'funds', 'furniture', 'fußball', 'game', 'games', 'gaming', 'gas', 'genomics',
    'gold', 'graines', 'graphene', 'graphite', 'grundstueck', 'grundstuecksauktionen', 'guitar', 'gym', 'hafen',
    'harbour', 'health', 'healthcare', 'homes', 'hosting', 'hotel', 'hoteliere', 'hotels', 'house', 'hydrogen',
    'hydrogene', 'hôtels', 'imaging', 'immobilien', 'immobiliare','immobiliere', 'immunotherapeutics', 'imprimerie', 'income',
    'industriali', 'industries', 'industry', 'informationssysteme', 'informationstechnologien', 'informatique',
    'infrastructure', 'instruments', 'insurance', 'internet', 'invest', 'investment', 'investments', 'investors', 'it',
    'judges', 'keller', 'klinik', 'kliniken', 'klinikum', 'land', 'laser', 'law', 'learning', 'lease', 'leasing', 'legal',
    'lending', 'licht', 'life', 'linguistic', 'lithium', 'logistics', 'logistik', 'markets', 'materials', 'media',
    'medical', 'meditec', 'medizintechnik', 'metal', 'metals', 'meunerie', 'microsystems', 'mineral', 'minerals',
    'mining', 'money', 'mortgage', 'motor', 'motors', 'multimédia', 'municipal', 'music', 'networking', 'news',
    'nutrition', 'oil', 'oncology', 'optical', 'optik', 'orthopaedics', 'packaging', 'pay', 'payment', 'payments',
    'petroleum', 'pharma', 'pharmaceuticals', 'phone', 'piscines', 'plant', 'plumbing', 'post', 'potash', 'power', 'pr',
    'privatbank', 'properties', 'property', 'publishing', 'radio', 'real', 'refueling', 'reit', 'renovables', 'rents',
    'research', 'residential', 'resources', 'retail', 'rohstoff', 'sante', 'savings', 'sea', 'securities', 'security',
    'semiconductor', 'sensor', 'settlement', 'shark', 'ship', 'shipping', 'shop', 'signaux', 'smartbroker', 'software',
    'solar', 'spirits', 'sports', 'stock', 'storage', 'strahlen', 'supermarket', 'surgical', 'tabak', 'telcom',
    'telekom', 'telemàtics', 'television', 'textil', 'textilhaus', 'therapeutics', 'tobacco', 'tour', 'tourisme',
    'traders', 'trading', 'traffic', 'training', 'truck', 'trust', 'tunnel', 'utilities', 'venture', 'vermoegen',
    'vertrieb', 'volt', 'voyageurs', 'warehouse', 'web', 'wechsel', 'wind', 'wine', 'wirtschaftsberatung', 'wohnen',
    'wood', 'woods']

common_words_in_company_names = ['abc', 'access', 'accessoires', 'accident', 'active', 'ad', 'advanced', 'affluent', 'agile',
                                 'aim', 'air', 'alien', 'alfa', 'alpha', 'alten', 'alternative', 'amadeus', 'amplitude',
                                 'animal', 'animation', 'applied', 'arm', 'arms', 'artificial', 'associated', 'auction',
                                 'automatismes', 'avenir', 'balanced', 'bars', 'basic', 'beach', 'bear', 'believe',
                                 'bell', 'benchmark', 'beta', 'big', 'black', 'block', 'blue', 'body', 'bois', 'bond',
                                 'boot', 'boss', 'bowl', 'box', 'brain', 'brand', 'brands', 'brave', 'broad', 'brothers',
                                 'brown', 'bulk', 'bunch', 'bureau', 'business', 'bytes', 'cab', 'cake', 'cap',
                                 'capital',
                                 'card', 'cash', 'centers', 'central', 'centre', 'chain', 'chapters', 'character',
                                 'cherry', 'city', 'class', 'clean', 'close', 'cloud', 'club', 'cohort', 'colours',
                                 'commerce', 'commercial', 'compagnie', 'companies', 'company', 'concept', 'content',
                                 'core', 'counter', 'counties', 'cpu', 'creation', 'critical', 'crest', 'dar', 'data',
                                 'database', 'debenture', 'del', 'delta', 'desarollo', 'deutsche', 'develop',
                                 'development',
                                 'developments', 'diploma', 'direct', 'discovery', 'doctor', 'dolfines', 'dragon',
                                 'dynamics', 'developpement', 'dynamic', 'e-solutions', 'earth', 'ecclesiastical', 'edel', 'efficiency',
                                 'emerging', 'empiric', 'encres', 'endurance', 'enterprise', 'entreprises', 'equity', 'ernst',
                                 'espace', 'essential', 'etablissements', 'events', 'exclusive', 'express', 'eye',
                                 'fachmarkt', 'facilities', 'factory', 'far', 'fast', 'feedback', 'fidelity', 'fill', 'fine',
                                 'fire', 'first', 'fit', 'flow', 'fluid', 'focus', 'foresight', 'frames', 'fusion', 'future',
                                 'gamma',
                                 'gateway', 'general', 'generale', 'genius', 'global', 'going', 'golden', 'good', 'gpu',
                                 'great', 'green', 'grid', 'ground', 'grounds', 'growth', 'hero', 'high', 'hill',
                                 'home', 'hospitality', 'hybrid', 'image', 'impact', 'industrial', 'industrielle',
                                 'industries', 'information', 'init', 'initial', 'innovacion', 'innovation',
                                 'innovations', 'inspiration', 'inspired', 'instrument', 'intelligence', 'intelligent',
                                 'interactive', 'international', 'internationale', 'intl.', 'intuitive', 'judges',
                                 'just', 'international', 'intl.',
                                 'king', 'klassik', 'koninklijke', 'lady', 'leg', 'libero', 'life', 'lifestyle',
                                 'light', 'lila', 'line', 'link', 'location', 'logic', 'love', 'made', 'maison',
                                 'making', 'managed', 'management', 'maps', 'mare', 'marks', 'maschine', 'median',
                                 'mensch', 'mercantile', 'metrics', 'metro', 'metropole', 'mind', 'mission', 'mister', 'mittelstand', 'mobile',
                                 'mobility', 'modisch', 'moment', 'monde', 'morgan', 'motive', 'mountain', 'mountainview', 'naked',
                                 'national', 'nationwide', 'natural', 'net', 'network', 'networks', 'new', 'noble',
                                 'north', 'nostrum', 'octopus', 'office', 'offshore', 'one', 'opportunities', 'opportunity',
                                 'optimization', 'orange', 'pacte', 'palace', 'pantheon', 'panther', 'parent',
                                 'partners', 'partnerships', 'patrimoine', 'pension', 'pepper', 'perfect', 'personal', 'pets',
                                 'pharmacy', 'phone', 'plan', 'planet', 'plant', 'plaza', 'plus', 'point', 'polar', 'polymer',
                                 'precious', 'premier', 'pressure', 'primary', 'prime', 'principles', 'private',
                                 'products', 'produktion', 'profitable', 'progress', 'prospect', 'protection', 'proven',
                                 'public', 'quality', 'rank', 'rapid', 'rational', 'reach', 'react', 'record', 'red',
                                 'regional', 'regionale', 'renew', 'resource', 'restore', 'revolution', 'river',
                                 'robot', 'rock', 'rocket', 'royal', 'safe', 'sage', 'saint', 'scan', 'scharf',
                                 'schloss', 'schwarz', 'science', 'sciences', 'scientific', 'secure', 'senior',
                                 'sensor', 'service', 'services', 'seven', 'shareholder', 'shell', 'silence', 'silver',
                                 'sistemas', 'sit', 'site', 'sleep', 'small', 'smaller', 'smart', 'smiths', 'social',
                                 'society', 'sole', 'solid', 'solution', 'solutions', 'sound', 'sources', 'special',
                                 'specialty', 'spielvereinigung', 'splendid', 'spoon', 'sport', 'standard', 'star',
                                 'state', 'stop', 'strategic', 'streams', 'strip', 'student', 'supply', 'sure',
                                 'surface', 'sustainable', 'systems', 'tandem', 'target', 'tec', 'tech', 'technologies',
                                 'technology', 'the', 'tier', 'tissue', 'titan', 'tornado', 'totally', 'tower', 'town', 'triple',
                                 'try', 'union', 'united', 'universal', 'up', 'urban', 'vacuum', 'value', 'values',
                                 'van', 'vast', 'venture', 'vereinigte', 'vertical', 'via', 'vision', 'water', 'werke',
                                 'west',
                                 'wild', 'work', 'workshop', 'world', 'yard', 'yellow', 'young', 'zone']


abbrevs_and_company_suffixes_all = list(
    set(abbreviations +
        abbrevs_numerals +
        abbrevs_titles +
        company_suffixes_legal_form +
        company_suffixes_industry_hints +
        company_name_bindings +
        abbrevs_lengths +
        abbrevs_numerals +
        abbrevs_titles))

abbrevs_and_company_suffixes_with_dot_at_end = [exp for exp in abbrevs_and_company_suffixes_all if exp[-1] == '.']

if __name__ == '__main__':
    # from src.utils.regex_funcs import clean_accents_and_umlaute
    #
    # res = [clean_accents_and_umlaute(t) for t in company_suffixes_legal_form]
    # print(sorted(list(set(res))))
    print(sorted(abbrevs_and_company_suffixes_with_dot_at_end))
    # for country in countries:
    #     if not country.istitle():
    #         print(country)
