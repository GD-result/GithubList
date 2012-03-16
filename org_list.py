import xmlrpclib
import requests
import json

from conf import SPACE
from conf import TOP_PAGE
from conf import WIKI_USER
from conf import WIKI_PASS
from conf import page_name
from conf import wiki_url
from conf import org_name
from conf import use_token
from conf import oauth_token
from conf import github_login
from conf import github_pass

class getList:
    wiki_server = xmlrpclib.ServerProxy(wiki_url)
    wiki_token = wiki_server.confluence1.login(WIKI_USER, WIKI_PASS)
        
    def get_list(self,list_url):
        """
        get_list(list_url)
        
        This function get the list of repositories/teams/users with chosen authorization type 
        """
        
        auth_type = ""
        if use_token:
            list_url += "?access_token=" + oauth_token
        else:
            auth_type = (github_login, github_pass)
        r = requests.get(url = list_url, auth = auth_type)
        if (r.status_code == requests.codes.OK):
            return json.loads(r.content)
        else:
            print "Error ",r.headers, r.status_code
            return None
    
    def request(self, content, name_page, wiki_token, wiki_server):
            """
            request(content, name_page, wiki_token, wiki_server)
            This function sends the content to the specified wiki page
            and create a new page, if this page does not exist
            Input:
            content - Required unicode
            name_page - Required unicode
            wiki_token - Required string
            wiki_server - Required instance
            """
            try:
                page = wiki_server.confluence1.getPage(wiki_token, SPACE, name_page)
            except:
                parent = wiki_server.confluence1.getPage(wiki_token, SPACE, TOP_PAGE)
                page = {
                      'parentId': parent['id'],
                      'space': SPACE,
                      'title': name_page,
                      'content': content
                      }
                wiki_server.confluence1.storePage(wiki_token, page)
            else:
                page['content'] = content
                wiki_server.confluence1.updatePage(wiki_token, page, {'versionComment':'','minorEdit':1})
                

    def main(self):
        host = "https://api.github.com/"
        list_url = host + "orgs/%s/repos" % org_name
        repos = self.get_list(list_url)
        if repos == None:
            print "Error. Failed to get the list of repositories"
            return
        content = "h1. Github users list (by repositories) \n\
        {html}<div class='table-wrap'>\n<table class = 'confluenceTable'>\n\
        <tr><th class='confluenceTh'>Repositories</th>\
        <th class='confluenceTh'>Teams</th>\
        <th class='confluenceTh'>Users</th>\
        </tr>"
        users_table = dict ()
        for repo in enumerate(repos):
            list_url = host + "repos/%s/%s/teams" % (org_name, repo[1]['name'])
            teams = self.get_list(list_url)
            if teams == None:
                print "Error. Failed to get the list of teams ", repo[1]['name']
                return
            if teams == []:
                content += "<tr><td class='confluenceTd'>%s<td class='confluenceTd'>&nbsp</td><td class='confluenceTd'>&nbsp</td></tr>" % (repo[1]['name'])
            else:
                content += "<tr><td rowspan='%d' class='confluenceTd'>%s</td>"\
                 % (len(teams),repo[1]['name'])
                for team in enumerate(teams):
                    content += "<td class='confluenceTd'>%s&nbsp</td>\
                    <td class='confluenceTd'>" % team[1]['name']
                    list_url = host + "teams/%s/members" % team[1]['id']
                    users = self.get_list(list_url)
                    if users == None:
                        print "Error. Failed to get the list of users ", team[1]['name']
                        return
                    if users != []:
                        for user in enumerate(users):
                            content += user[1]['login'] + ", "
                            if repo[1]['private']:
                                row = "<td class='confluenceTd'><b>%s</b></td><td class='confluenceTd'>%s</td></tr>" % (repo[1]['name'],team[1]['name'])
                            else: 
                                row = "<td class='confluenceTd'>%s</td><td class='confluenceTd'>%s</td></tr>" % (repo[1]['name'],team[1]['name'])
                            if users_table.has_key(user[1]['login']):
                                users_table.update({user[1]['login']: (users_table.get(user[1]['login'])[0] + "<tr>" + row, users_table.get(user[1]['login'])[1] + 1)})
                            else:
                                users_table.update({user[1]['login']: (row, 1)})
                        content = content[:-2]
                    content += "&nbsp</td></tr>"
        content += "</table></div>{html}\n \
        h1. Github users list (by users)\n\
        {html}<div class='table-wrap'>\n<table class = 'confluenceTable'>\n\
        <tr><th class='confluenceTh'>Users</th>\
        <th class='confluenceTh'>Repositories</th>\
        <th class='confluenceTh'>Teams</th>\
        </tr>"
        for key, value in sorted(users_table.items()):
            content += "<tr><td rowspan = '%s' class='confluenceTd'>" % (value[1]) + key + "</td>" + value[0]
        content += "</table></div>{html}"
        self.request(content, page_name, self.wiki_token, self.wiki_server)
        
getList = getList()
getList.main()        