import os
import time
import parsel
import requests
import math
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import unquote
from multiprocess import Pool
from functools import partial

referer = 'http://agefans.org/'
header = {
    'Cookie': '__cfduid=d9216f203c70cad8785fd8f10dcf2fb5d1594952490; csrftoken=OBJWjqkshWbI1IGirAjQqa9IKy9KOBp9T1a16N6GrA5qTcTdc4azooNitiumjxYA',
    'Host': 'agefans.org',
    'Referer': referer,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.40'
}

path = './Spider' # 视频储存位置
video_url = {}  # 搜索到的视频信息
episodes_url = {}  # 视频下载地址
episodes_urls = {}  #分段视频链接
rel_path = ''

def request(url):
    r = requests.get(url, headers=header)
    r.raise_for_status()
    r.encoding = 'utf-8'
    return r

def print_info(url):  # 输出搜索到的视频信息
    html = request(url).text
    search_info = parsel.Selector(html).xpath('//*[@id="search_list"]/ul//div[@class="card-body p-2"]').extract()
    Serial = 0
    if not search_info:
        print("什么都没有找到!")
        return
    for info in search_info:
        Serial += 1
        soup = BeautifulSoup(info, 'html.parser')
        video_url[soup.a.h5.string] = 'http://agefans.org' + soup.a.attrs['href']
        print("{:0>2d}:\t《 ".format(Serial) + soup.a.h5.string + ' 》')
        for div in soup.find_all('div', {'class': ''}):
            print('\t' + div.span.string + div.span.next_sibling.next_sibling.string)
        num = 0
        for li in soup.find_all('li'):
            num += 1
            if num % 2 != 0:
                print('\t' + li.span.string + li.span.next_sibling.next_sibling.string, end='')
            else:
                print('\t' + li.span.string + li.span.next_sibling.next_sibling.string)
        intro = soup.find('div', {'class': 'ellipsis_summary catalog_summary small'})
        try:
            print('\t' + intro.span.string + intro.span.next_sibling.next_sibling.string.replace('\n', '') + '...')
        except Exception:
            content = str(intro.span.next_sibling.next_sibling).replace('\n', '').replace('<span>', '').replace(
                '<br/>', '').replace('</span>', '').replace('&lt;', '') + '...'
            print('\t' + intro.span.string + content)
        print('\n' + '=' * 30 + '\n')

def get_new_url(info, referer, rel_path, name, video_url):
    li = BeautifulSoup(info, 'html.parser')
    url = 'http://agefans.org/myapp/_get_ep_plays?{}&anime_id={}'.format(li.a.attrs['href'].split('_', 1)[-1].replace('_', '='), video_url[name].split('/')[-1])
    referer = video_url[name] + li.a.attrs['href']
    ID_dict = {}
    counter = 0
    for result in request(url).json()['result']:
        ID_dict['ID' + str(counter)] = result['id']
        counter += 1
    for ID in ID_dict.values():
        try:
            new_url = 'http://agefans.org/myapp/_get_e_i?url={}&quote=1'.format(ID)
            if unquote(request(new_url).json()['result']).startswith('https://') or unquote(request(new_url).json()['result']).startswith('http://') or unquote(request(new_url).json()['result']).startswith('//'):
                episodes_url[li.a.string.replace(' ', '')] = unquote(request(new_url).json()['result'])
            else:
                continue
        except Exception:
            try:
                new_url = 'http://agefans.org/myapp/_get_mp4s?id={}'.format(ID)
                url_lists = request(new_url).json()
                if url_lists:
                    episodes_urls.setasdefault(li.a.string.replace(' ', ''), []).append(url_lists)
                else:
                    new_url = 'http://agefans.org/myapp/_get_raw?id={}'.format(ID)
                    download_url = request(new_url).text
                    if download_url.startswith('https://') or download_url.startswith('http://') or download_url.startswith('//'):
                        episodes_urls.setdefault(li.a.string.replace(' ', ''), []).append(download_url)
                    else:
                        continue
            except Exception as e:
                print(type(e), e)
    full_url = episodes_url | episodes_urls
    return full_url

def get_relurl(name): # 爬取动漫视频网址
    global referer, rel_path
    rel_path = path + '/' + name
    if os.path.exists(rel_path):
        pass
    else:
        os.makedirs(rel_path)
    referer = video_url[name]
    html = request(video_url[name]).text
    all_li = parsel.Selector(html).xpath('//div[@id="plays_list"]/ul/li').extract()
    pool = Pool(len(all_li))
    new_url_partial = partial(get_new_url, referer = referer, rel_path = rel_path, name = name, video_url = video_url)
    results = list(tqdm(pool.imap(new_url_partial, all_li), total = len(all_li), desc = "正在获取视频链接..."))
    for urldict in results:
        position = results.index(urldict)
        urldict['position'] = position
        results[position] = urldict
    print(results)
    return rel_path, results

def write_file(url, filename, position, name):
    try:
        if url.startswith('//'):
            url = 'https:' + url
        if url.endswith('.m3u8'):
            pass
        r = requests.get(url, stream = True)
        total_size = int(r.headers.get('content-length'))
        if total_size < 1024 * 1024:
            pass
        else:
            with open(filename, 'wb') as f:
                for chunk in tqdm(r.iter_content(10 * 1024 * 1024), desc = "正在下载: " + name + "...", total=math.ceil(total_size / (10 * 1024 * 1024)),unit='10MB', unit_scale=True, position = position + 1):
                    if chunk:
                        f.write(chunk)
                stop = True
                return stop
    except Exception as e:
        print(type(e), e)

def video_download(s_dict, rel_path): # 下载视频，如果视频小于1MB就删除视频
    position = s_dict['position']
    del s_dict['position']
    for name in s_dict.keys():
        filename = rel_path + '/' + name + '.mp4'
        filename_2 = rel_path + '/' + name + '2' + '.mp4'
        if isinstance(s_dict[name], list):
            for epi_url in s_dict[name]:
                if isinstance(epi_url, list):
                    for sep_url in epi_url:
                        if os.path.exists(filename):
                            stop = write_file(sep_url, filename_2, position, name)
                            if stop: break
                        else:
                            stop = write_file(sep_url, filename, position, name)
                            if stop: break
                else:
                    stop = write_file(epi_url, filename, position, name)
                    if stop: break
        else:
            stop = write_file(s_dict[name], filename, position, name)
            if stop: break
    return

def user_ui():
    print('#' * 25 + '\tAGE动漫离线助手\t' + '#' * 25)
    keyword = input('请输入搜索关键字：')
    url = 'http://agefans.org/search?q=' + keyword
    print_info(url)
    choice = int(input('请输入序号选择：'))
    name = list(video_url.keys())[choice - 1]
    start = time.time()
    rel_path, full_array = get_relurl(name)
    pool = Pool(len(full_array) + 1)
    download_func = partial(video_download, rel_path = rel_path)
    list(tqdm(pool.imap(download_func, full_array), desc = "正在下载: " + name + "...", total = len(full_array), position = 0))
    pool.close()
    pool.join()
    end = time.time()
    print("下载完成！共耗时：{}分钟".format((end - start) / 60))

if __name__ == '__main__':
    user_ui()
