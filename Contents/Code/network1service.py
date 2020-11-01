import sys
sys.path.insert(0,'D:\Plex\Plex Media Server\Plug-ins\MetaDataHelper')
import re
import MyHelper
import PAsearchSites
import PAgenres
import PAactors
import PAutils

missingNames = {'Sexy black MILF licks Belarus babe':['Jasmine Webb'],
                'Hot Euro girls clit licking orgasms': ['Aislin'],
                'Model fucks horny photographer': ['Jasmine Webb'],
                'Yoga lesbian centipede pussy eating': ['Arian Joy','Aislin'],
                'Ebony and Latina pussy stacking sex': ['Jasmine Webb'],
                'Gardener satisfies Ebony housewife': ['Jasmine Webb','Steve Q'],
                'Pillow fight before lesbian sex': ['Shona River'],
                'Black MILF demands pussy licking': ['Jasmine Webb','Dom Ully'],
                'Experienced brunette loves cock': ['Dom Ully'],
                'Babes in sexy lingerie and leotard': ['Anie Darling'],
                'Sexy Euro angels oil soaked ecstasy': ['Aislin'],
                'Naughty girl spanked by Stepmom': ['Aislin'],
                'Interracial lesbians wet and oiled': ['Nathaly Cherie'],
                'Brunette seduces cheating therapist': ['Dorian Del Isla'],
                'Brunette seduces cheating therapist': ['Sweet Cat'],
                'Soft skin natural body lesbians 69': ['Aislin'],
                'Big tits babelicious Czech princess': ['Vanessa Decker','Stirling Cooper'],
                'Black temptress gobbles chunky cock': ['Jasmine Webb', 'Michael Fly'],
                'Cock hungry big butt black girl': ['Jasmine Webb', 'Michael Fly'],
                'Busty gym babe\'s big cock threesome': ['Angel Wicky'],
                'Shower Curtain Glory Hole Surprise': ['Ashley Aleigh','Seth Gamble'],
                'Paper Plate': ['Brian Omally'],
                'Halloween Bash': ['Nicole Bexley'],
                'Sexy Solah': ['Brick Danger']}

titleToSkipSearch = ['Cream On Me']
def get_Token(siteID):
    token_key = None
    if siteID == 2 or (siteID >= 54 and siteID <= 81) or siteID == 582 or siteID == 690:
        token_key = 'brazzers_token'

    token = None
    if token_key and token_key in Dict:
        data = Dict[token_key].split('.')[1] + '=='
        data = base64.b64decode(data).decode('UTF-8')
        if json.loads(data)['exp'] > time.time():
            token = Dict[token_key]

    if not token:
        req = PAutils.HTTPRequest(PAsearchSites.getSearchBaseURL(siteID), 'HEAD')
        if 'instance_token' in req.cookies:
            token = req.cookies['instance_token']

    if token_key and token:
        if token_key not in Dict or Dict[token_key] != token:
            Dict[token_key] = token
            Dict.Save()

    return token


def search(results, encodedTitle, searchTitle, siteNum, lang, searchDate):
    token = get_Token(siteNum)
    headers = {
        'Instance': token,
    }

    sceneID = None
    splited = searchTitle.split(' ')
    if unicode(splited[0], 'UTF-8').isdigit():
        sceneID = splited[0]
        searchTitle = searchTitle.replace(sceneID, '', 1).strip()

    Log('******Search CALLED*******')
    Log('******encodedTitle******* ' + str(encodedTitle))
    Log('******sceneID******* ' + str(sceneID))
    Log('******searchTitle******* ' + str(searchTitle))
    Log('******siteNum******* ' + str(siteNum))

    for sceneType in ['scene', 'movie', 'serie', 'trailer']:
        if sceneID and not searchTitle:
            url = PAsearchSites.getSearchSearchURL(siteNum) + '/v2/releases?type=%s&id=%s' % (sceneType, sceneID)
        else:
            url = PAsearchSites.getSearchSearchURL(siteNum) + '/v2/releases?type=%s&search=%s' % (sceneType, encodedTitle)

        req = PAutils.HTTPRequest(url, headers=headers)
        if req:
            searchResults = req.json()['result']
            for searchResult in searchResults:
                titleNoFormatting = searchResult['title']
                releaseDate = parse(searchResult['dateReleased']).strftime('%Y-%m-%d')
                curID = searchResult['id']
                siteName = searchResult['brand'].title()
                Log('******titleNoFormatting******* ' + str(titleNoFormatting))
                Log('******releaseDate******* ' + str(releaseDate))
                Log('******curID******* ' + str(curID))
                Log('******siteName******* ' + str(siteName))
                subSite = ''
                if 'collections' in searchResult and searchResult['collections']:
                    subSite = searchResult['collections'][0]['name']
                siteDisplay = '%s/%s' % (siteName, subSite) if subSite else siteName

                if sceneID:
                    score = 100 - Util.LevenshteinDistance(sceneID, curID)
                elif searchDate:
                    score = 100 - Util.LevenshteinDistance(searchDate, releaseDate)
                else:
                    score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())

                if sceneType == 'trailer':
                    titleNoFormatting = '[%s] %s' % (sceneType.capitalize(), titleNoFormatting)
                    score = score - 10

                results.Append(MetadataSearchResult(id='%s|%d|%s' % (curID, siteNum, sceneType), name='%s [%s] %s' % (titleNoFormatting, siteDisplay, releaseDate), score=score, lang=lang))

    return results

mapTaglineToStudio = {'Look At Her Now':'Reality Kings'}

def update(metadata,siteID,movieGenres,movieActors):
    Log('******UPDATE CALLED*******')
    Log('******metadata******* ' + str(metadata))
    Log('******siteID******* ' + str(siteID))
    Log('******movieGenres******* ' + str(movieGenres))
    Log('******movieActors******* ' + str(movieActors))

def update(metadata, siteID, movieGenres, movieActors):
    metadata_id = str(metadata.id).split('|')
    sceneID = metadata_id[0]
    sceneType = metadata_id[2]

    token = get_Token(siteID)
    headers = {
        'Instance': token,
    }
    url = PAsearchSites.getSearchSearchURL(siteID) + '/v2/releases?type=%s&id=%s' % (sceneType, sceneID)
    Log('******url******* ' + str(url))
    req = PAutils.HTTPRequest(url, headers=headers)
    detailsPageElements = req.json()['result'][0]
    Log('******detailsPageElements******* ' + str(detailsPageElements))

    # Studio
    studio = detailsPageElements['brand'].title()
    Log('******studio******* ' + studio)
    studio = MyHelper.getStudio(studio)
    Log('******studio******* ' + studio)
    realStudio = None
    try:
        realStudio = mapTaglineToStudio[studio]
    except:
        pass

    if realStudio is None:
        metadata.studio = MyHelper.getStudio(studio)
        metadata.collections.add(metadata.studio)
    else:
        metadata.studio = realStudio
        metadata.collections.add(realStudio)
        metadata.tagline = studio
        metadata.collections.add(studio)
    metadata.studio = detailsPageElements['brand'].title()

    # Tagline and Collection(s)
    metadata.collections.clear()
    seriesNames = []
    preTitle = ''

    if 'collections' in detailsPageElements and detailsPageElements['collections']:
        for collection in detailsPageElements['collections']:
            seriesNames.append(collection['name'])
    if 'parent' in detailsPageElements:
        if 'title' in detailsPageElements['parent']:
            seriesNames.append(detailsPageElements['parent']['title'])

    isInCollection = False
    siteName = PAsearchSites.getSearchSiteName(siteID).lower().replace(' ', '').replace('\'', '')
    for seriesName in seriesNames:
        if seriesName.lower().replace(' ', '').replace('\'', '') == siteName:
            isInCollection = True
            break

    if not isInCollection:
        seriesNames.insert(0, PAsearchSites.getSearchSiteName(siteID))

    for seriesName in seriesNames:
        seriesName = MyHelper.getStudio(seriesName)
        if 'Flixxx' in seriesName:
            preTitle = seriesName + ': ';
        if 'Rawcut' in seriesName:
            seriesName = 'Raw Cuts'
            preTitle = seriesName + ': ';
        if 'Digital Playground' not in studio:
            metadata.tagline = seriesName.replace('BellesaHouse', 'Bellesa Films')
        metadata.collections.add(seriesName)

    #
    # try:
    #     #metadata.extras.clear()
    #     trailer_url = str(detailsPageElements['videos']['mediabook']['files']['720p']['urls']['view'])
    #     Log('******trailer_url******* ' + str(trailer_url))
    #     extra = TrailerObject(
    # 				url = 'https://www.youtube.com/watch?v=pbJZb0j_aXg&ab_channel=CumOnFace',
    # 				title = 'trailer',
    # 				thumb = 'https://media-public-ht.project1content.com/m=eaSaaTbWx/780/53f/2a2/0fa/4cf/891/edf/f2b/3f9/768/ac/poster/poster_01.jpg'
    # 			)
    #     Log('******extra******* ' + str(extra))
    #     metadata.extras.add(extra)
    # except:
    #     pass

    # Rating
    rating = str(detailsPageElements['stats']['score'])
    Log('*******rating****** ' + rating)
    metadata.rating = float(rating) * 10

    # Title
    metadata.title = preTitle + detailsPageElements['title']
    title = metadata.title

    # Summary
    description = None
    if 'description' in detailsPageElements:
        description = detailsPageElements['description']
    elif 'parent' in detailsPageElements:
        if 'description' in detailsPageElements['parent']:
            description = detailsPageElements['parent']['description']

    if description:
        metadata.summary = description

    # Release Date
    date_object = parse(detailsPageElements['dateReleased'])
    metadata.originally_available_at = date_object
    metadata.year = metadata.originally_available_at.year

    # Director
    try:
        Log('*******Finding Dirctory****** ' + str(len(metadata.directors)))
        searchTitle = re.sub('([^:]*)?(:|Scene|Episode|Part).*', r'\1', metadata.title)
        searchTitle = searchTitle.strip()
        Log('*******Finding Director****** ' + searchTitle)
        if 'Digital Playground' in metadata.studio:
            Log('*******is ****** Digital Playground')
            MyHelper.findDirector(searchTitle, metadata.year, metadata)
    except:
        pass

    # Genres
    movieGenres.clearGenres()
    genres = detailsPageElements['tags']
    for genreLink in genres:
        genreName = genreLink['name']
        movieGenres.addGenre(genreName)

    # Actors
    # Find others
    actorSet = set([])
    actor2photo = {}
    if metadata.title not in titleToSkipSearch:
        Log('*******Search For Actors******: ' + str(metadata.title) + ' : ' + str(metadata.year))
        try:
            actor2photo = MyHelper.findActors(metadata.title, metadata.year, metadata, Log)
        except:
            pass
        Log('*******Found Actors******: ' + str(actor2photo))

    if len(actor2photo) == 0:
        Log('*******Cleared Actors******: ')
        actors = detailsPageElements['actors']
        for actorLink in actors:
            actorPageURL = PAsearchSites.getSearchSearchURL(siteID) + '/v1/actors?id=%d' % actorLink['id']

            req = PAutils.HTTPRequest(actorPageURL, headers=headers)
            actorData = req.json()['result'][0]

            actorName = actorData['name']
            actorPhotoURL = ''
            if actorData['images'] and actorData['images']['profile']:
                actorPhotoURL = actorData['images']['profile'][0]['xs']['url']

            movieActors.addActor(actorName, actorPhotoURL)
            Log('*******Added Actor******: ' + actorName)
    else:
        for name, photo in actor2photo.items():
            movieActors.addActor(name, photo)

    Log('*******Missing Names******: ' + title)
    try:
        for name in missingNames[title]:
            Log('*******Missing Names Found For******: ' + name)
            photo = MyHelper.getPhoto(name, metadata.year, ' ')
            movieActors.addActor(name, photo)
            Log('Member Photo Url : ' + photo)
    except:
        pass

    # Posters
    art = []
    for imageType in ['poster', 'cover']:
        if imageType in detailsPageElements['images']:
            for image in detailsPageElements['images'][imageType]:
                art.append(image['xx']['url'])

    Log('Artwork found: %d' % len(art))
    for idx, posterUrl in enumerate(art, 1):
        if not PAsearchSites.posterAlreadyExists(posterUrl, metadata):
            # Download image file for analysis
            try:
                image = PAutils.HTTPRequest(posterUrl, headers={'Referer': 'http://www.google.com'})
                im = StringIO(image.content)
                resized_image = Image.open(im)
                width, height = resized_image.size
                # Add the image proxy items to the collection
                if width < height:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(image.content, sort_order=idx)
                if width > 100 and width > height:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(image.content, sort_order=idx)
            except:
                pass

    return metadata
