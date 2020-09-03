# -*- coding: utf-8 -*
import requests
import json

"""
请求封装类
"""

class Requestutil():

    def __init__(self):
        pass

    def request(self, url: object, method: object, headers: object = None, data: object = None, content_type: object = None) -> object:
        """
        通用请求工具类
        :param url:
        :param method:
        :param headers:
        :param param:
        :param content_type:
        :return:
        """
        try:
            if method == "get":
                result = requests.get(url=url,data=data,headers=headers).json()
                print(result)
                return result
            elif method == "post":
                if content_type == "application/josn":
                    result = requests.post(url=url,json=data,headers=headers).json()
                    return result
                if content_type == "multipart/form-data":
                    result = requests.post(url=url, json=data, headers=headers).json()
                    return result
                else:
                    result = requests.post(url=url, data=data, headers=headers).json()
                    return result

            else:
                print("http method not allowed")

        except Exception as e:
            print("http请求报错:{0}".format(e))

if __name__ == '__main__':
    pass
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = "http://114.115.138.124:28081/"
    r = Requestutil()
    result = r.request(url,'get',data={})
    print(result)
    # data = {"phone": "13113777555", "pwd": "1234567890"}

    # result = r.request(url, 'post', param=data, headers=headers)
    # print(result)

