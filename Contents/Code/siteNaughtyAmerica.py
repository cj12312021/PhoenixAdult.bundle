import sys
sys.path.insert(0,'A:\Plex\Plex Media Server\Plug-ins\MetaDataHelper')
from datetime import datetime as altdatetime
import MyHelper
import PAsearchSites
import PAgenres
import PAutils

missingNames = {'Casey Calvert fucking in the living room with her brown eyes':['Chad White'],
                'Wife Lexi Belle fucking in the couch with her black hair':['Ryan Mclane'],
                'Gracie Glam fucking in the living room with her big ass':['Xander Corvus'],
                'Client Annie Cruz fucking in the couch with her piercings':['Tim Cannon'],
                'Mia Malkova fucking in the floor with her small tits':['Chad White'],
                'Jillian Janson fucking in the floor with her blue eyes':['Ryan Mclane'],
                'Brooke Wylde fucking in the yoga studio with her hazel eyes':['Ryan Mclane'],
                'Wife Brooke Wylde fucking in the chair with her blue eyes': ['Richie Black']}

fixNames = {'Dakota':'Dakota Skye',
            'Clover': 'Clover M',
            'Tony Desergio':'Tony De Sergio',
            'Christian':'Christian XXX'}

def getAlgolia(url, indexName, params):
    params = json.dumps({'requests': [{'indexName': indexName, 'params': params + '&hitsPerPage=100'}]})
    headers = {
        'Content-Type': 'application/json'
    }
    data = PAutils.HTTPRequest(url, headers=headers, params=params).json()

    return data['results'][0]['hits']


def search(results, encodedTitle, searchTitle, siteNum, lang, searchDate):
    sceneID = searchTitle.split(' ', 1)[0]
    if unicode(sceneID, 'UTF-8').isdigit():
        searchTitle = searchTitle.replace(sceneID, '', 1).strip()
    else:
        sceneID = None

    url = PAsearchSites.getSearchSearchURL(siteNum) + '?x-algolia-application-id=I6P9Q9R18E&x-algolia-api-key=08396b1791d619478a55687b4deb48b4'
    if sceneID and not searchTitle:
        searchResults = getAlgolia(url, 'nacms_scenes_production', 'filters=id=' + sceneID)
    else:
        searchResults = getAlgolia(url, 'nacms_scenes_production', 'query=' + searchTitle)

    for searchResult in searchResults:
        titleNoFormatting = searchResult['title']
        curID = searchResult['id']
        releaseDate = datetime.fromtimestamp(searchResult['published_at']).strftime('%Y-%m-%d')
        siteName = searchResult['site']

        if sceneID:
            score = 100 - Util.LevenshteinDistance(sceneID, curID)
        elif searchDate:
            score = 100 - Util.LevenshteinDistance(searchDate, releaseDate)
        else:
            score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())

        results.Append(MetadataSearchResult(id='%d|%d' % (curID, siteNum), name='%s [%s] %s' % (titleNoFormatting, siteName, releaseDate), score=score, lang=lang))

    return results


def update(metadata, siteID, movieGenres, movieActors):
    metadata_id = str(metadata.id).split('|')
    sceneID = metadata_id[0]

    url = PAsearchSites.getSearchSearchURL(siteID) + '?x-algolia-application-id=I6P9Q9R18E&x-algolia-api-key=08396b1791d619478a55687b4deb48b4'
    detailsPageElements = getAlgolia(url, 'nacms_scenes_production', 'filters=id=' + sceneID)[0]

    # Title
    title = detailsPageElements['title']
    metadata.title = title

    # Summary
    metadata.summary = detailsPageElements['synopsis']

    # Studio
    metadata.studio = 'Naughty America'

    # Tagline and Collection(s)
    metadata.collections.clear()
    metadata.tagline = detailsPageElements['site']
    metadata.collections.add(metadata.tagline)
    metadata.collections.add(metadata.studio)

    # Release Date
    Log('*******published_at******: ' + str(detailsPageElements['published_at']))
    date_object = datetime.fromtimestamp(detailsPageElements['published_at'])
    metadata.originally_available_at = date_object
    metadata.year = metadata.originally_available_at.year

    # Genres
    movieGenres.clearGenres()
    genres = detailsPageElements['fantasies']
    if 'Virtual Reality' in genres:
        #Nov 20, 2020
        SixKResDate = altdatetime.strptime('November 20, 2020', '%B %d, %Y')
        FourKResDate = altdatetime.strptime('March 1, 2018', '%B %d, %Y')
        if date_object >= SixKResDate:
            movieGenres.addGenre('6K')
        elif date_object >= FourKResDate:
            movieGenres.addGenre('4K')
        else:
            movieGenres.addGenre('3K')
        movieGenres.addGenre('180°')


    for genreLink in genres:
        genreName = genreLink

        movieGenres.addGenre(genreName)

    req = PAutils.HTTPRequest('https://www.naughtyamerica.com/scene/0' + sceneID)
    scenePageElements = HTML.ElementFromString(req.text)

    # Actors
    movieActors.clearActors()
    for actorLink in scenePageElements.xpath('//a[@class="scene-title grey-text link"]'):
        actorName = actorLink.text
        try:
            actorName = fixNames[actorName]
        except:
            pass
        Log('*******actorName******: ' + actorName)
        actorPhotoURL = ''

        actorsPageURL = 'https://www.naughtyamerica.com/pornstar/' + actorName.lower().replace(' ', '-').replace(
            "'", '')
        req = PAutils.HTTPRequest(actorsPageURL)
        actorsPageElements = HTML.ElementFromString(req.text)
        img = actorsPageElements.xpath('//img[@class="performer-pic"]/@src')
        if img:
            actorPhotoURL = 'https:' + img[0]

        movieActors.addActor(actorName, actorPhotoURL)
    # actorLinks = detailsPageElements['performers']
    # if actorLinks > 0:
    #     for actorLink in detailsPageElements['performers']:
    #         actorName = actorLink
    #         try:
    #             actorName = fixNames[actorName]
    #         except:
    #             pass
    #         Log('*******actorName******: ' + actorName)
    #         actorPhotoURL = ''
    #
    #         actorsPageURL = 'https://www.naughtyamerica.com/pornstar/' + actorName.lower().replace(' ', '-').replace("'", '')
    #         req = PAutils.HTTPRequest(actorsPageURL)
    #         actorsPageElements = HTML.ElementFromString(req.text)
    #         img = actorsPageElements.xpath('//img[@class="performer-pic"]/@src')
    #         if img:
    #             actorPhotoURL = 'https:' + img[0]
    #
    #         movieActors.addActor(actorName, actorPhotoURL)
    # else:
    #     for actorLink in scenePageElements.xpath('//a[@class="scene-title grey-text link"]'):
    #         actorName = actorLink.text
    #         try:
    #             actorName = fixNames[actorName]
    #         except:
    #             pass
    #         Log('*******actorName******: ' + actorName)
    #         actorPhotoURL = ''
    #
    #         actorsPageURL = 'https://www.naughtyamerica.com/pornstar/' + actorName.lower().replace(' ', '-').replace(
    #             "'", '')
    #         req = PAutils.HTTPRequest(actorsPageURL)
    #         actorsPageElements = HTML.ElementFromString(req.text)
    #         img = actorsPageElements.xpath('//img[@class="performer-pic"]/@src')
    #         if img:
    #             actorPhotoURL = 'https:' + img[0]
    #
    #         movieActors.addActor(actorName, actorPhotoURL)


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

    for photo in scenePageElements.xpath('//div[contains(@class, "contain-scene-images") and contains(@class, "desktop-only")]/a/@href'):
        img = 'https:' + re.sub(r'images\d+', 'images1', photo, 1, flags=re.IGNORECASE)
        art.append(img)
        if 'vertical/390x590cdynamic.jpg' in img:
            art.append(img.replace('vertical/390x590cdynamic.jpg','horizontal/1000x563c.jpg'))

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
