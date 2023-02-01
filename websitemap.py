from urllib.parse import urlparse
import json
from collections import defaultdict
from threading import Lock


class QueryMap():
    def __init__(self):
        #dict of query_name -> count
        self.query_param_counts = defaultdict(int)
        #dict of val -> count
        self.query_val_counts   = defaultdict(int)
        
    def get_param_counts(self):
        return self.query_param_counts

    def get_val_counts(self):
        return self.query_val_counts

    def insert_param(self, param):
        self.query_param_counts[param] += 1
    
    def insert_val(self, val):
        self.query_val_counts[val] += 1


class WebsiteMap():
    def __init__(self):
        #map of website -> queries
        self.map = defaultdict(defaultdict)

        #map of queries -> websites
        #self.reverse_map = defaultdict(defaultdict)

        #contains query_param_counts and query_val_counts 
        #query_param_counts: dict of query_name -> count
        #query_val_counts:   dict of val -> count
        self.query_map = QueryMap()

        self.lock = Lock()


    #checks if the url has already been visited
    #if strict is enabled then we dont consider new parameter values to be a new url
    def visited(self, url, strict=False):

        entry = self.generate_entry_from_url(url)

        visited = self.search(entry, self.map, strict)

        return visited

    #checks if destination is inside source
    def search(self, source, destination, strict=False):
        
        #for each key,value pair in the level
        for key, value in source.items():

            if isinstance(value, dict) and strict:
                #next level, equal to value
                if key not in destination:
                    return False

                node = destination.setdefault(key, {})

                if not self.search(value, node, strict):
                    return False

            elif isinstance(value, int) and strict:

                if key not in destination:
                    return False

            #not strict
            elif any(isinstance(i,dict) for i in value.values()) and not strict:

                #next level, equal to value
                if key not in destination:
                    return False

                node = destination.setdefault(key, {})

                if not self.search(value, node, strict):
                    return False

            #not strict
            elif not strict:
                #print("key here: " + key)
                #self.display(destination)
                #self.display(source)

                if key not in destination:
                    return False

            else:
                print("Unkown condition, returning False")
                return False

            return True

        
    #adds an entry to the map
    def add_entry(self, url):
        
        if url == None:
            return

        entry = self.generate_entry_from_url(url)

        self.lock.acquire()
        self.map = self.merge_entries(self.map, entry)
        self.lock.release()

    def add_entries(self, urls):
        for url in urls: self.add_entry(url)


    #merges two recursive dictionaries
    def merge_entries(self, source, destination):
        
        #for each key,value pair in the level
        for key, value in source.items():
            if isinstance(value, dict):
                #next level, equal to value
                node = destination.setdefault(key, {})
                self.merge_entries(value, node)
            else:
                if key not in destination:
                    destination[key] = source[key]
                else: 
                    destination[key] += source[key]

        return destination

    def generate_entry_from_url(self, url): 
        #parse the url
        parsed_url = urlparse(url)

        #generate flattened hierarchy from url
        path = self.generate_hierarchy(url) 

        entry = {}
        e = entry

        for idx in range(len(path)):
            e = e.setdefault(path[idx], {})

            #final path
            if idx == (len(path)-1):
                e = e.setdefault("queries", defaultdict(lambda: defaultdict(int)))
                queries = self.generate_query_entry(parsed_url.query)
                
                for param, vals in queries.items():
                    for val in vals:
                        e[param][val] += 1

                        self.query_map.insert_param(param)
                        self.query_map.insert_val(val)

        return entry

    #gets a list of queries given a url 
    def get_query_params(self, url=None):
        
        if not url: return self.query_map.get_param_counts()

        path = self.generate_hierarchy(url) 

        query_params = defaultdict(lambda: defaultdict(int))

        self.lock.acquire()

        query_params = self.collect_query_params(path, self.map, query_params)

        self.lock.release()

        return query_params


    def collect_query_params(self, path, entry, query_params):

        #for each key,value pair in the level
        for key, value in entry.items():
            if len(path) and isinstance(value, dict):
                current_dir = path[0] 

                #correct subdir
                if current_dir == key:
                    self.search(path[1:], value, query_params)

            else:
                if key == "queries":
                    #for each query
                    for param, values in value.items():
                        
                        #for each query value and count
                        for value, count in values.items():

                            query_params[param][value] += count 


                else: 
                    self.search([], value, query_params)

        return query_params


    def get_query_vals(self, url=None):
        if not url: return self.query_map.get_val_counts()

        path = self.generate_hierarchy(url) 
        
    #generate flattened hierarchy from url
    def generate_hierarchy(self, url):
        #parse the url
        parsed_url = urlparse(url)

        #generate hierarchy
        path = list(filter(None, [parsed_url.netloc] + parsed_url.path.split("/")[1:]))

        return path

    def generate_query_entry(self, query):
        #queries = defaultdict(lambda: defaultdict(int))
        queries = defaultdict(list)

        try:
            for q in query.split("&"): 
                param_name, value = q.split("=")
                #queries[param_name][value] += 1
                queries[param_name].append(value)
        except:
            return queries

        return queries
    
    def display(self, m=None):
        if not m: m=self.map
        print(json.dumps(m, indent=4))



if __name__ == "__main__":
    webmap = WebsiteMap()

    entry = 'https://google.com'
    webmap.add_entry(entry)

    webmap.display()

    print(webmap.visited(entry, strict=False))

