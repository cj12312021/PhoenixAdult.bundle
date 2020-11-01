import PAsearchSites
import re
import MyHelper
from datetime import datetime
import PAgenres
import PAactors
import PAutils


missingNames = {'Stella Cox in Black Meat White Feet':['Flash Brown'],
                'Brittney White in We Fuck Black Girls': ['Kurt Lockwood','Chris Strokes'],
                'Karlee Grey in Cuckold Sessions': ['Rico Strong', 'Jc Power'],
                'Goddess Kyra in We Fuck Black Girls': ['Xander Corvus'],
                'Nikki Ford in We Fuck Black Girls': ['Mr Pete','Erik Everhard']}
def search(results, encodedTitle, searchTitle, siteNum, lang, searchDate):
    encodedTitle = searchTitle.replace(' a ', ' ')

    req = PAutils.HTTPRequest(PAsearchSites.getSearchSearchURL(siteNum) + encodedTitle)
    searchResults = HTML.ElementFromString(req.text)
    for searchResult in searchResults.xpath('//a[contains(@class, "thumbnail")]'):
        titleNoFormatting = searchResult.xpath('.//h3[@class="scene-title"]')[0].text_content().strip()
        curID = PAutils.Encode(searchResult.get('href').split('?')[0])
        releaseDate = parse(searchDate).strftime('%Y-%m-%d') if searchDate else ''
        fullSubSite = searchResult.xpath('.//div/p[@class="help-block"]')[0].text_content().strip()

        if 'BehindTheScenes' in fullSubSite and 'BTS' not in titleNoFormatting:
            titleNoFormatting = titleNoFormatting + ' BTS'
        subSite = fullSubSite.split('.com')[0]

        if subSite == PAsearchSites.getSearchSiteName(siteNum):
            score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())
        else:
            score = 60 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())

        results.Append(MetadataSearchResult(id='%s|%d|%s' % (curID, siteNum, releaseDate), name='%s [Dogfart/%s]' % (titleNoFormatting, subSite), score=score, lang=lang))

    return results


def update(metadata, siteID, movieGenres, movieActors):
    Log('******UPDATE CALLED*******')
    temp = str(metadata.id).split("|")[0].replace('_', '/').replace("$", "_")
    Log(temp)
    url = PAsearchSites.getSearchBaseURL(siteID) + temp
    Log(url)
    detailsPageElements = HTML.ElementFromURL(url)

    # Studio
    Log('*******Updating Studio******: ')
    metadata.studio = 'Dogfart'

    # Title
    Log('*******Updating Title******: ')
    metadata.title = detailsPageElements.xpath('//div[@class="icon-container"]/a')[0].get("title")
    Log('*******Title is ******: '+metadata.title)

    # Summary
    Log('*******Updating Summary******: ')
    metadata.summary = detailsPageElements.xpath('//div[contains(@class, "description")]')[0].text_content().strip().replace('...read more', '').replace('\n', ' ')

    # Collections / Tagline
    Log('*******Updating Tagline/Collections******: ')
    tagline = detailsPageElements.xpath('//h3[@class="site-name"]')[0].text.strip()
    Log('*******tagline is ******: '+tagline)
    metadata.tagline = re.sub(r"(\w)([A-Z])", r"\1 \2", tagline.replace('.com', ''))
    Log('*******Updated tagline is ******: ' + str(metadata.tagline))
    metadata.collections.clear()
    metadata.collections.add(metadata.studio)
    metadata.collections.add(metadata.tagline)

    # Release Date
    Log('*******Updating Release Date******: ')
    try:
        date = detailsPageElements.xpath('//meta[@itemprop="uploadDate"]')[0].get('content').replace('T00:00:00+07:00',
                                                                                                     '')
        if len(date) > 0:
            date_object = datetime.strptime(date, '%Y-%m-%d')
            metadata.originally_available_at = date_object
            metadata.year = metadata.originally_available_at.year
            Log("Date from file")
            Log('*******Updating Release Date is ******: '+str(metadata.originally_available_at))
    except:
        pass
    # if sceneDate:
    #     date_object = parse(sceneDate)
    #     metadata.originally_available_at = date_object
    #     metadata.year = metadata.originally_available_at.year

    # Actors
    Log('*******Updating Actors******: ')
    actorSet = set([])
    actor2photo = {}
    title = detailsPageElements.xpath('//h1[@class="description-title"]')[0].text
    metadata.title = title + ' in ' + metadata.tagline
    Log('*******New Title Actors******: '+metadata.title)
    title = title.replace('\'', '%27')
    studio = metadata.tagline.replace('-', ' ')
    search = studio.replace(' ', '+') + '%3a+' + title.replace('&', 'and').replace(' ', '+') + '/year=' + str(
        metadata.year)
    search = search.lower()
    Log('*******Search For Actors: ' + str(search) + ' : ' + str(metadata.year))
    try:
        actor2photo = MyHelper.findActors(search, metadata.year, metadata, Log)
    except:
        pass
    Log('*******Found Actors******: ' + str(actor2photo))
    metadata.roles.clear()
    if len(actor2photo) == 0:
        actors = detailsPageElements.xpath('//h4[@class="more-scenes"]/a')
        if len(actors) > 0:
            for actorLink in actors:
                actorName = str(actorLink.text_content().strip())
                actorPhotoURL = ''
                movieActors.addActor(actorName, actorPhotoURL)
    else:
        for name, photo in actor2photo.items():
            role = metadata.roles.new()
            s = name.split(" - ")
            Log('*******actor******: ' + str(s))
            role.name = s[0]
            try:
                role.role = s[1]
            except:
                pass
            actorSet.add(role.name)
            role.photo = photo

    # add missing actor names
    Log('*******Missing Names******: ' + metadata.title)
    try:
        for name in missingNames[metadata.title]:
            role = metadata.roles.new()
            role.name = MyHelper.getActor(name)
            actorSet.add(name)
            role.photo = MyHelper.getPhoto(role.name, metadata.year, ' ')
            Log('Member Photo Url : ' + role.photo)
    except:
        pass

    # Genres
    genres = detailsPageElements.xpath('//div[@class="categories"]/p/a')
    if len(genres) > 0:
        for genreLink in genres:
            genreName = genreLink.text_content().strip('\n').lower()
            movieGenres.addGenre(genreName)

        Log('*******Searching Genre******')
        genreSet = MyHelper.findGenre(None, metadata.year, list(actorSet), True)
        Log('*******Found Genre******: ' + str(genreSet))
        for genre in genreSet:
            metadata.genres.add(genre)
        Log('Genre Sequence Updated ')

    # Rating
    try:
        rating = detailsPageElements.xpath('//span[@itemprop="ratingValue"]')[0].text
        Log('*******rating****** ' + rating)
        metadata.rating = float(rating)
    except Exception as e:
        Log(e)

    # Posters
    art = []
    xpaths = [
        '//div[@class="icon-container"]//img/@src'
    ]
    for xpath in xpaths:
        for img in detailsPageElements.xpath(xpath):
            art.append(img)

    for pageURL in detailsPageElements.xpath('//div[contains(@class, "preview-image-container")]//a/@href'):
        req = PAutils.HTTPRequest(PAsearchSites.getSearchBaseURL(siteID) + pageURL)
        posterPage = HTML.ElementFromString(req.text)

        posterUrl = posterPage.xpath('//div[contains(@class, "remove-bs-padding")]/img/@src')[0]
        art.append(posterUrl)

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
                if width > height:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(image.content, sort_order=idx)
                else:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(image.content, sort_order=idx)
            except:
                pass

    return metadata
