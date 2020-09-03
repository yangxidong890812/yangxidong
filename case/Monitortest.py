# -*- coding: utf-8 -*
import time
import datetime
import json
from Interface_test_automation.db.db_utils import MysqlDb
from Interface_test_automation.utils.requsts_util import Requestutil
from Interface_test_automation.utils.send_email import SendMail


class MonitorTestCase():

    def AllCaseByProject(self,project):
        """
        根据project项目加载全部测试用例
        :param project:
        :return:
        """
        # 实例化
        project_db = MysqlDb()
        sql = "select * from `case` where app = '{0}'".format(project)
        results = project_db.query(sql)
        return results



    def FindCaseById(self,case_id):
        """
        根据用例id找测试用例
        :param case_id:
        :return:
        """
        project_db = MysqlDb()
        sql = "select * from `case` where id='{0}'".format(case_id)
        results = project_db.query(sql,state="one")
        return results

    def loadConfigByAppAndKey(self, project, key):
        """
        根据project项目和key加载配置
        :param app:
        :param key:
        :return:
        """
        project_db = MysqlDb()
        sql = "select * from `config` where app='{0}' and dict_key='{1}'".format(project, key)
        results = project_db.query(sql, state="one")
        return results


    def updateResultByCaseId(self, response, is_pass, msg, case_id):
        """
        根据测试用例id，更新响应内容和测试内容
        :param response:
        :param is_pass:
        :param msg:
        :param case_id:
        :return:
        """
        project_db = MysqlDb()
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # sql = "update `case` set response=\"{0}\", pass='{1}', msg='{2}', update_time='{3}' where id={4}".format(
        #     str(response), is_pass, msg, current_time, case_id)

        if is_pass:
            sql = "update `case` set response=\'{0}\', pass='{1}', msg='{2}', update_time='{3}' where id={4}".format("",
                                                                                                                   is_pass,
                                                                                                                   msg,
                                                                                                                   current_time,
                                                                                                                   case_id)

        else:
            sql = "update `case` set response=\"{0}\", pass='{1}', msg='{2}', update_time='{3}' where id={4}".format(
                str(response), is_pass, msg, current_time, case_id)
        rows = project_db.execute(sql)

        return rows


    def runAllCase(self, project):
        """
        执行全部用例的入口
        :param project:
        :return:
        """
        # 获取接口域名
        api_host_obj = self.loadConfigByAppAndKey(project, "host")
        # 获取全部用例
        results = self.AllCaseByProject(project)

        for case in results:
            # print(case)
            if case['run'] == 'yes':
                try:

                    # 执行用例
                    response = self.runcase(case, api_host_obj)
                    # 断言判断
                    assert_msg = self.assertResponse(case, response)

                    # 更新结果存储数据库
                    rows = self.updateResultByCaseId(response, assert_msg['is_pass'], assert_msg['msg'], case['id'])

                    print("更新结果 rows={0}".format(str(rows)))

                except Exception as e:
                    print("用例id={0},标题:{1},执行报错:{2}".format(case['id'], case['title'], e))
                    pass

        # 发送测试报告

        self.sendTestReport(project)


    def runcase(self, case, api_host_obj):
        # 执行单个测试用例
        headers = json.loads(case['headers'])
        body = json.loads(case['request_body'])
        method = case['method']
        req_url = api_host_obj['dict_value'] + case['url']

        pre_fields = json.loads(case['pre_fields'])

        for pre_field in pre_fields:

            if pre_field['scope'] == 'header' and case["pre_case_id"] != 1:
                # 遍历headers ,替换对应的字段值，即寻找同名的字段
                for header in headers:
                    field_name = pre_field['field']
                    if header == field_name:
                        self.field_value = self.response ['entity']
                        headers[field_name] = self.field_value

            elif case["pre_case_id"] == 1:
                # 遍历headers ,替换对应的字段值，即寻找同名的字段
                for header in headers:

                    field_name = pre_field['field']
                    if header == field_name:
                        headers[field_name] = self.field_value

            elif case["pre_case_id"] == 2:
                # 遍历headers ,替换对应的字段值，即寻找同名的字段
                for header in  headers:
                    field_name = pre_field['field']
                    if header == field_name:
                        self.field_value = self.response['entity']
                        headers[field_name] = self.field_value





        req = Requestutil()
        self.response = req.request(req_url, method, headers=headers, data=body)
        return self.response



    def assertResponse(self, case, response):
        """
        断言响应内容，更新用例执行情况 {"is_pass":true, "msg":"code is wrong"}
        :param case:
        :param response:
        :return:
        """

        assert_type = case['assert_type']
        expect_result = case['expect_result']
        # assert_type = 'resultCode'
        #
        # expect_result = "0"
        is_pass = False

        # 判断业务状态码
        if assert_type == 'resultCode':
            response_code = response['result']['resultCode']

            if (expect_result) == response_code:
                is_pass = True
                print("测试用例通过")
            else:
                print("测试用例不通过")
                is_pass = False

        # 判断数组长度大小
        elif assert_type == 'data_json_array':
            data_array = response['data']
            if data_array is not None and isinstance(data_array, list) and len(data_array) > int(expect_result):
                is_pass = True
                print("测试用例通过")
            else:
                print("测试用例不通过")
                is_pass = False
        elif assert_type == 'data_json':
            data = response['data']
            if data is not None and isinstance(data, dict) and len(data) > int(expect_result):
                is_pass = True
                print("测试用例通过")
            else:
                print("测试用例不通过")
                is_pass = False

        msg = "模块:{0}, 标题:{1},断言类型:{2},响应:{3}".format(case['module'], case['title'], assert_type, response['result']['resultMessage'])
        # 拼装信息
        assert_msg = {"is_pass": is_pass, "msg": msg}
        # print(assert_msg)
        return assert_msg

    def sendTestReport(self, project):
        """
        发送邮件，测试报告
        :param app:
        :return:
        """
        print("sendTestReport")

        # 加载全部测试用例
        results = self.AllCaseByProject(project)
        title = "新监控后台接口自动化测试报告"
        content = """
        <html><body>
            <h4>{0} 接口测试报告：</h4>
            <table border="1">
            <tr>
              <th>编号</th>
              <th>模块</th>
              <th>标题</th>
              <th>是否通过</th>
              <th>备注</th>
              <th>响应</th>
            </tr>
            {1}
            </table></body></html>  
        """
        template = ""
        for case in results:

            template += "<tr><td>{0}</td><td>{1}</td><td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>".format(
                case['id'], case['module'], case['title'], case['pass'], case['msg'], case['response']
            )

        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        content = content.format(current_time, template)
        mail_host = self.loadConfigByAppAndKey(project, "mail_host")['dict_value']
        mail_sender = self.loadConfigByAppAndKey(project, "mail_sender")['dict_value']
        mail_auth_code = self.loadConfigByAppAndKey(project, "mail_auth_code")['dict_value']
        mail_receivers = self.loadConfigByAppAndKey(project, "mail_receivers")['dict_value'].split(",")
        mail = SendMail(mail_host)
        mail.send(title, content, mail_sender, mail_auth_code, mail_receivers)







if __name__ == '__main__':
    test = MonitorTestCase()
    test.runAllCase('新监控后台')
    # test.updateResultByCaseId("ok",True,"haha",2)
    # a = {'entity': 'eyJhbGciOiJIUzUxMiJ9.eyJleHAiOjE1OTkwOTYzMDUsInVzZXIiOiJ7XCJhcHBJZFwiOjAsXCJsZXZlbENvZGVcIjpcIlwiLFwidXNlcklkXCI6XCIwNTdiOTQxZS1iODM3LTQwYWMtOTRhMy02NTVlOGY3MTVlY2FcIixcInVzZXJOYW1lXCI6XCIwNTdiOTQxZS1iODM3LTQwYWMtOTRhMy02NTVlOGY3MTVlY2FcIixcInVzZXJSZWFsTmFtZVwiOlwiXCIsXCJ1c2VyVHlwZVwiOlwiZ3Vlc3RcIixcInV1aWRcIjpcIjBlMWZiN2NjLTdiMDQtNGIyMy1iYjU0LWVmMDIyZjAwOTMzN1wifSJ9.aNie5Ope2Afr7Xj1HXpdcAW-bZ5vIrNkah5RGWow6PfDE5ngLxltPbi20o9_lK2zS0kI3ikvHH1FPSq2WRvXjA', 'result': {'resultCode': '0', 'resultMessage': '执行成功'}}
    # test.assertResponse("新监控后台",a)

