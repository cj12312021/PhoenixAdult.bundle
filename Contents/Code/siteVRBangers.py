# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,'A:\Plex\Plex Media Server\Plug-ins\MetaDataHelper')
import MyHelper
import PAsearchSites
import PAgenres
import urllib
import PAutils
import re

def search(results, encodedTitle, searchTitle, siteNum, lang, searchDate):
    req = PAutils.HTTPRequest(PAsearchSites.getSearchSearchURL(siteNum) + encodedTitle)
    searchResults = HTML.ElementFromString(req.text)
    for searchResult in searchResults.xpath('//article'):
        titleNoFormatting = searchResult.xpath('.//a[@rel="bookmark"]')[0].text_content().strip()
        curID = PAutils.Encode(searchResult.xpath('.//a/@href')[0])

        score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())

        if len(titleNoFormatting) > 29:
            titleNoFormatting = titleNoFormatting[:32] + '...'

        results.Append(MetadataSearchResult(id='%s|%d' % (curID, siteNum), name='%s [%s]' % (titleNoFormatting, PAsearchSites.getSearchSiteName(siteNum)), score=score, lang=lang))

    return results

def findPoster(title):
    original_title = re.sub('^(A|The)\s', '', title)
    Log('findPoster original_title: ' + original_title)
    title = title.replace(':','').replace('’','').replace('#','').replace('&','').replace('?','').replace('*','')
    Log('findPoster title: ' + title)
    value = {'fq': title}
    Log('findPoster value: ' + str(value))
    value = urllib.urlencode(value)
    Log('findPoster encodeValue: ' + str(value))
    url = 'https://www.adultempire.com/94792/studio/vrbangers-studios.html?media=14&' + value
    Log('findPoster url: ' + str(url))
    html = MyHelper.getHTML(url)
    for image in  html.xpath('//div[@class="boxcover-container"]/a/img'):
        original_title = original_title.lower().replace('’', '')
        original_title = re.sub('[,#!?&’\':;\-"()]', '', original_title)
        compare = image.get('title').lower().replace('\'', '')
        compare = re.sub('[,#!?&’\':;\-"()]', '', compare)
        if original_title in compare:
            return image.get('data-src').replace('m.jpg','h.jpg')

def update(metadata, siteID, movieGenres, movieActors):
    metadata_id = str(metadata.id).split('|')
    sceneURL = PAutils.Decode(metadata_id[0])
    if not sceneURL.startswith('http'):
        sceneURL = PAsearchSites.getSearchBaseURL(siteID) + sceneURL
    req = PAutils.HTTPRequest(sceneURL)
    detailsPageElements = HTML.ElementFromString(req.text)

    # Title
    metadata.title = detailsPageElements.xpath('//h1')[0].text_content().strip()

    # Summary
    try:
        metadata.summary = detailsPageElements.xpath('//div[@class="less-text d-block"]/p[2]')[0].text_content().strip()
    except:
        pass

    # Studio
    metadata.studio = 'VR Bangers'

    # Tagline and Collection
    metadata.collections.clear()
    tagline = PAsearchSites.getSearchSiteName(siteID)
    metadata.tagline = tagline
    metadata.collections.add(metadata.studio)

    # Release Date
    date = detailsPageElements.xpath('//div[@class="video-content__download-info"]//div[@class="section__item-title-download-space"][2]')[0].text_content().replace('Release date:', '').strip()
    if date:
        date_object = parse(date)
        metadata.originally_available_at = date_object
        metadata.year = metadata.originally_available_at.year

    # Genres
    movieGenres.clearGenres()
    resolution = detailsPageElements.xpath('//span[@class="video-item--quality_res"]')[0].text
    Log('Resolution: ' + resolution)
    degree = detailsPageElements.xpath('//div[@class="section__item-title-download-space section__item-title-download-space-opened"]')[0].text_content()
    degree = degree.replace('Degree:','').strip()+'°'
    Log('degree: ' + degree)
    format = detailsPageElements.xpath('//div[@class="section__item-title-download-space section__item-title-download-space-opened"]')[3].text_content()
    format = format.replace('Format:', '').strip()
    if 'VR' in format:
        format = '2D'
    Log('format: ' + format)
    movieGenres.addGenre(resolution)
    movieGenres.addGenre(degree)
    movieGenres.addGenre(format)
    for genreLink in detailsPageElements.xpath('//div[contains(@class,"video-item-info-tags")]//a'):
        genreName = genreLink.text_content().strip()

        movieGenres.addGenre(genreName)
    movieGenres.addGenre('VR')

    # Actors
    movieActors.clearActors()
    for actorLink in detailsPageElements.xpath('//div[@class="video-content__download-info"]//div[contains(@class,"video-item-info--starring")]//a'):
        actorName = actorLink.text_content().strip()

        actorPageURL = actorLink.get('href')
        req = PAutils.HTTPRequest(actorPageURL)
        actorPage = HTML.ElementFromString(req.text)
        actorPhotoURL = actorPage.xpath('//img[contains(@class, "single-model__featured-img")]/@src')[0]

        movieActors.addActor(actorName, actorPhotoURL)

    # Posters
    art = []
    xpaths = [
        '//a[contains(@class, "justified__item")]/@href'
    ]

    for xpath in xpaths:
        for img in detailsPageElements.xpath(xpath):
            art.append(img)

    Log('Artwork found: %d' % len(art))
    i = 1
    posterUrl = ''
    try:
        Log('Finding poster.')
        posterUrl = findPoster(str(metadata.title))
        Log('posterUrl: ' + posterUrl)
        metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content,
                                              sort_order=i)
    except:
        pass
    i = i + 1
    try:
        posterUrl = detailsPageElements.xpath('//dl8-video')[0].get('poster')
        Log('Background: ' + posterUrl)
        metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order=i)
        i=i+1
    except:
        pass
    try:
        posterUrl = detailsPageElements.xpath('//img[@class="object-fit-cover img-parallax-inside"]')[0].get('data-pagespeed-lazy-src')
        metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content,
                                              sort_order=i)
        i = i + 1
    except:
        pass
    for idx, posterUrl in enumerate(art, i):
        if not PAsearchSites.posterAlreadyExists(posterUrl, metadata):
            # Download image file for analysis
            try:
                image = PAutils.HTTPRequest(posterUrl, headers={'Referer': 'http://www.google.com'})
                im = StringIO(image.content)
                resized_image = Image.open(im)
                width, height = resized_image.size
                # Add the image proxy items to the collection
                if height > width:
                    # Item is a poster
                    metadata.posters[posterUrl] = Proxy.Media(image.content, sort_order=idx)
                else:
                    # Item is an art item
                    metadata.art[posterUrl] = Proxy.Media(image.content, sort_order=idx)
            except:
                pass

    return metadata
