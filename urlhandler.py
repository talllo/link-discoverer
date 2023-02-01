import re
from urllib.parse import urlparse

class UrlHandler():
    def __init__(self, url, allowed_domains=[], allowed_paths=[], disallowed_paths=[], allowed_params=[], allowed_queries=[], allowed_fragments=[]):
        self.url_regex = UrlRegex(
                        allowed_domains   = allowed_domains,
                        allowed_paths     = allowed_paths,
                        disallowed_paths  = disallowed_paths,
                        allowed_params    = allowed_params,
                        allowed_queries   = allowed_queries,
                        allowed_fragments = allowed_fragments)
        self.url = url
        self.base_url = "https://" + urlparse(url).netloc


    def set_base_url(self, url):

        #add http
        if "http" not in url[0:5]: url = "https://" + url

        self.url = url
        self.base_url = "https://" + urlparse(url).netloc


    def fix_url(self, url):

        if url[0:2] == "//": url = url[2:]
        elif url[0] == "/": url = self.base_url+url

        return url

    def is_valid_url(self, url):

        if not len(url): return False
        
        url = self.fix_url(url)
        
        return self.url_regex.is_valid_url(url)

#mutatable url object using urlparse
class UrlRegex():
    def __init__(self, allowed_domains=[], allowed_paths=[], disallowed_paths=[], allowed_params=[], allowed_queries=[], allowed_fragments=[]):
        #allow https or http as schema
        self.allowed_schemes      = re.compile("(^$|https|http)")

        #allow any subdomains for urlname
        self.allowed_domains      = self.generate_allowed_domains(allowed_domains)

        #allowed paths
        self.allowed_paths        = self.generate_allowed_paths(allowed_paths)

        #disallowed paths
        self.disallowed_paths     = self.generate_disallowed_paths(disallowed_paths)

        #self.allowed_params      = self.generate_allowed_params(allowed_params)

        self.allowed_queries      = self.generate_allowed_queries(allowed_queries)
        #self.allowed_fragments   = re.compile("")


    def from_url(self, url, override_allowed_domains=[], override_allowed_path=[]):

        regex = UrlRegex()
        parsed_url = urlparse(url)

        #allow https or http as schema
        regex.allowed_schemes      = re.compile("(^$|https|http)")

        #generate subdomains regex
        regex.allowed_domains = regex.generate_allowed_domains([parsed_url.netloc] + override_allowed_domains)

        #generate allowed_paths regex
        regex.allowed_paths = regex.generate_allowed_paths([parsed_url.path] + override_allowed_path)

        #generate queries regex
        queries = [query.split("=")[0] for query in parsed_url.query.split("&")]
        regex.allowed_queries      = regex.generate_allowed_queries(queries)

        return regex

    def is_valid_url(self, url):
        parsed_url = urlparse(url)
        a = self.allowed_schemes.search(parsed_url.scheme)
        b = self.allowed_domains.search(parsed_url.netloc)
        c = self.allowed_paths.search(parsed_url.path)
        d = None 
        if self.disallowed_paths != None:
            d = self.disallowed_paths.search(parsed_url.path)
        #print(self.allowed_schemes)
        #print(self.allowed_domains)
        #print(parsed_url.netloc)
        #print(self.allowed_paths)

        #v = (a != None) and (b != None) and (c != None) and (d == None)
        #print(url)
        #print(v)

        #print("\nschemes: " + str(a))
        #print("domains: " + str(b))
        #print("paths: " + str(c))

        #c = self.allowed_queries.findall(parsed_url.query) 

        return (a != None) and (b != None) and (c != None) and (d == None)
        
    def generate_allowed_queries(self, allowed_queries=[]):
        #any url domain name allowed
        if len(allowed_queries) == 0: return re.compile(r"(\w)\=[^&\s.]*")

        return self.generate_regex(r"({REGEX})\=[^&\s.]+", [urlparse(url_domain).path for url_domain in allowed_queries])


    def generate_allowed_paths(self, allowed_paths=[]):
        #any url domain name allowed
        if len(allowed_paths) == 0: return re.compile(r"[\\/]{0,1}(\/.*)([\\/\.\w]{1})*")

        return self.generate_regex(r"[\\/]{{0,1}}({REGEX})([\\/\.\w]{{1}})*", [urlparse(url_domain).path for url_domain in allowed_paths])

    def generate_disallowed_paths(self, disallowed_paths=[]):
        #any url domain name allowed
        if len(disallowed_paths) == 0: return None

        return self.generate_regex(r"[\\/]{{0,1}}({REGEX})([\\/\.\w]{{1}})*", [urlparse(url_domain).path for url_domain in disallowed_paths])


    def generate_allowed_domains(self, allowed_domains=[]):
        #any url domain name allowed
        if len(allowed_domains) == 0: return re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z]")

        return self.generate_regex(r"(([-_a-zA-Z0-9]+[\.])*({REGEX}))[\/]{{0,1}}", [urlparse(url_domain).path for url_domain in allowed_domains])


    def generate_regex(self, regex, options):

        re_string = r""

        for url_domain in options: re_string+=regex.format(REGEX=url_domain) +"|"
        
        return re.compile(re_string[:-1])

#base_url = "https://www.acronis.com/en-us/" 
#
#handler =  UrlHandler(base_url,
#                    allowed_domains=["acronis.com"],
#                    allowed_paths=[".*"],
#                    disallowed_paths=["en-us"],
#                    allowed_params=[],
#                    allowed_queries=[],
#                    allowed_fragments=[])
#
#print(handler.is_valid_url("https://abgw-bud1-aci01.acronis.com/"))
#print(handler.is_valid_url("https://www.acronis.com/abc/123en-us/products/cloud/cyber-protect/security/"))
#print(handler.is_valid_url("https://www.acronis.com/products/cloud/cyber-protect/security/"))


