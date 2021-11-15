# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import selenium
import random
import time
from selenium import webdriver
import redis
import json

redis_client = redis.Redis(db=5)
main_page_url = 'https://www.jd.com/'

search_element = '/html/body/div[1]/div[4]/div/div[2]/div/div[2]/input'
search_confirm_btn = '/html/body/div[1]/div[4]/div/div[2]/div/div[2]/button'
xpath_product_list = '/html/body/div[5]/div[2]/div[2]/div[1]/div/div[2]/ul'
xpath_next_page = '/html/body/div[5]/div[2]/div[2]/div[1]/div/div[3]/div/span[1]/a[9]'
xpath_product_ul = '/html/body/div[5]/div[2]/div[2]/div[1]/div/div[2]/ul'
xpath_page_number = '/html/body/div[5]/div[2]/div[2]/div[1]/div/div[3]/div/span[2]/em[1]/b'
xpath_page_input = '/html/body/div[5]/div[2]/div[2]/div[1]/div/div[3]/div/span[2]/input'
xpath_confirm_page = '/html/body/div[5]/div[2]/div[2]/div[1]/div/div[3]/div/span[2]/a'


def parse_product_value_from_jd(product_list):
    for line_id in product_list:
        img_class = 'p-img'
        item_url = line_id.find_element_by_class_name(img_class).find_element_by_tag_name('a').get_property('href')
        item_img_url = line_id.find_element_by_class_name(img_class).find_element_by_tag_name(
            'a').find_element_by_tag_name('img').get_property('src')

        price_class = 'p-price'
        item_price_currency = line_id.find_element_by_class_name(price_class).find_element_by_tag_name('i').text
        item_price = line_id.find_element_by_class_name(price_class).find_element_by_tag_name('em').text

        commit_class = 'p-commit'
        item_commit = line_id.find_element_by_class_name(commit_class).find_element_by_tag_name('a').text
        shop_class = 'p-shop'
        item_shop_name = line_id.find_element_by_class_name(shop_class).find_element_by_tag_name('a').text
        name_class = 'p-name'
        item_name = line_id.find_element_by_class_name(name_class).find_element_by_tag_name('em').text
        try:
            item_bond = line_id.find_element_by_class_name(name_class).find_element_by_tag_name(
                'em').find_element_by_tag_name('font').text
        except Exception as e:
            item_bond = '-'
        item_sku = line_id.get_attribute('data-sku')
        item_summary = line_id.text
        payload_data = {
            'item_name': item_name,
            'item_bond': item_bond,
            'item_url': item_url,
            'item_img_url': item_img_url,
            'item_price_currency': item_price_currency,
            'item_price': item_price,
            'item_commit': item_commit,
            'item_shop_name': item_shop_name,
            'item_sku': item_sku,
            'item_summary': item_summary,
        }
        print('sku: {}'.format(item_sku))
        redis_client.set('JD:PRODUCT:{}'.format(item_sku), json.dumps(payload_data))


def scroll_web_driver(web_driver):
    web_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.randint(1, 3))
    web_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.randint(1, 3))
    web_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.randint(1, 3))
    web_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.randint(1, 3))
    return web_driver


def extract_product_value_from_jd(web_driver, current_page, max_retries=5):
    print('current page: {}'.format(current_page))
    try:
        if current_page != 1:
            web_driver = scroll_web_driver(web_driver)
            web_driver.find_element_by_xpath(xpath_page_input).clear()
            web_driver.find_element_by_xpath(xpath_page_input).send_keys(current_page)
            page_confirm_attr = web_driver.find_element_by_xpath(xpath_confirm_page)
            web_driver.execute_script(page_confirm_attr.get_attribute('onclick'))
        web_driver = scroll_web_driver(web_driver)
        product_ul = web_driver.find_element_by_xpath(xpath_product_ul)
        product_list = product_ul.find_elements_by_class_name('gl-item')
        parse_product_value_from_jd(product_list)

        print('Page [ {} ] done.'.format(current_page))
    except Exception as e:
        if max_retries > 1:
            extract_product_value_from_jd(web_driver, current_page, max_retries=max_retries - 1)
        else:
            print('error: {}'.format(e))
            print('当前页码 [{}] 数据异常'.format(current_page))


def search_product_by_keyword(search_keyword):
    driver = webdriver.Chrome('/home/jx/jd_product/chromedriver')
    driver.get(main_page_url)

    driver.find_element_by_xpath(search_element).clear()
    driver.find_element_by_xpath(search_element).send_keys(search_keyword)
    driver.find_element_by_xpath(search_confirm_btn).click()

    time.sleep(random.randint(3, 5))
    try:
        driver = scroll_web_driver(driver)
        page_number = driver.find_element_by_xpath(xpath_page_number).text
        for current_page in range(5, int(page_number) + 1):
            extract_product_value_from_jd(driver, current_page)
    except Exception as e:
        driver.close()
        raise e


if __name__ == '__main__':
    key_word = '鱼跃医疗'
    search_product_by_keyword(key_word)
    redis_client.close()
