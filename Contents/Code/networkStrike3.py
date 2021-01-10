import PAsearchSites
import urllib2 as urllib
import PAgenres
import PAutils


def getDatafromAPI(url):
    #req = PAutils.HTTPRequest(url)

    hdr = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Cookie': 'cf_chl_1=84bdddca0f71ebe; cf_chl_prog=x19; cf_clearance=48ca1f31fd7f0fc87a7bf8a70225ebc3768d9d6b-1604679878-0-1z143c1c85zf9513bbza40d28a2-150; __cfduid=d6cc64dee14297a8dabcadacc94831f081604679878; PHPSESSID=qarqef1aa0th2s6j066nlcjmt2svfgll; nats=NjI3LjYxLjMuMy4wLjAuMC4wLjA; nats_cookie=No%2BReferring%2BURL; nats_unique=NjI3LjYxLjMuMy4wLjAuMC4wLjA; nats_sess=3621881f8e077a58cdf29cbeff14d60f; nats_landing=No%2BLanding%2BPage%2BURL; vuid=ae55f4c6-9aa2-46fd-8457-34a4302c5717; sid=s%3AhC_nONiIbsLQL77L-XxZsug5dNIsyq_o.cInXxwuVXf%2FT16J3rYXJC46oSK3lyLQPLE%2Fn4C1sinQ'}
    req = urllib.Request(url, headers=hdr)
    req.encoding = 'UTF-8'

    if req:
        return req.json()['data']
    return req


def search(results, encodedTitle, searchTitle, siteNum, lang, searchDate):
    url = PAsearchSites.getSearchSearchURL(siteNum) + '/search?q=' + encodedTitle

    searchResults = getDatafromAPI(url)
    if searchResults:
        for searchResult in searchResults['videos']:
            titleNoFormatting = searchResult['title']
            releaseDate = parse(searchResult['releaseDate']).strftime('%Y-%m-%d')
            curID = PAutils.Encode(searchResult['targetUrl'])

            if searchDate:
                score = 100 - Util.LevenshteinDistance(searchDate, releaseDate)
            else:
                score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())

            results.Append(MetadataSearchResult(id='%s|%d' % (curID, siteNum), name='%s %s' % (titleNoFormatting, releaseDate), score=score, lang=lang))

    return results


def update(metadata, siteID, movieGenres, movieActors):
    metadata_id = str(metadata.id).split('|')
    sceneName = PAutils.Decode(metadata_id[0])
    sceneURL = PAsearchSites.getSearchSearchURL(siteID) + sceneName

    detailsPageElements = getDatafromAPI(sceneURL)
    video = detailsPageElements['video']
    pictureset = detailsPageElements['pictureset']

    # Title
    metadata.title = video['title']

    # Summary
    metadata.summary = video['description']

    # Director
    director = metadata.directors.new()
    director.name = video['directorNames']

    # Studio
    metadata.studio = video['primarySite'].title()

    # Tagline and Collection(s)
    metadata.collections.clear()
    metadata.collections.add(metadata.studio)

    # Release Date
    date_object = parse(video['releaseDate'])
    metadata.originally_available_at = date_object
    metadata.year = metadata.originally_available_at.year

    # Genres
    movieGenres.clearGenres()
    genres = video['tags']
    for genreName in genres:
        movieGenres.addGenre(genreName)

    # Actors
    movieActors.clearActors()
    actors = video['modelsSlugged']
    for actorLink in actors:
        actorPageURL = PAsearchSites.getSearchSearchURL(siteID) + '/' + actorLink['slugged']
        actorData = getDatafromAPI(actorPageURL)['model']

        actorName = actorData['name']
        actorPhotoURL = actorData['cdnUrl']

        movieActors.addActor(actorName, actorPhotoURL)

    # Posters
    art = []

    for name in ['movie', 'poster']:
        if name in video['images'] and video['images'][name]:
            image = video['images'][name][-1]
            if 'highdpi' in image:
                art.append(image['highdpi']['3x'])
            else:
                art.append(image['src'])
            break

    for image in pictureset:
        img = image['main'][0]['src']

        art.append(img)

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
                if width > 1 or height > width:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(image.content, sort_order=idx)
                if width > 100 and width > height and idx > 1:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(image.content, sort_order=idx)
            except:
                pass

    return metadata
