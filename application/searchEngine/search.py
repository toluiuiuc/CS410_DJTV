import json
import sys
import time
import shutil
import os
import metapy
import pytoml

movie_reviews = json.load(open('movie_reviews_dataset.json'))

# simple search
def search(search_param):
    # lower and strip leading + trailing white spaces
    search_param = search_param.strip().lower()
    # result dictionary
    titles = {}
    for movie_id in movie_reviews:
        localized_title = movie_reviews[movie_id]['localized_title'].lower()
        if search_param in localized_title:
            titles[movie_reviews[movie_id]['localized_title']] = movie_id
    return titles

def find_movies_with_year(year):
    movies = []
    for id in movie_reviews:
        if movie_reviews[id]['year'] == year:
            movies.append(movie_reviews[id]['localized_title'])
            print(movie_reviews[id]['localized_title'] + ' ' + str(movie_reviews[id]['year']))
        if len(movies) == 10:
            break
    print('')
    return movies

def find_movies_with_gte_rating(rating):
    movies = []
    for id in movie_reviews:
        if movie_reviews[id]['rating'] >= rating:
            movies.append(movie_reviews[id]['localized_title'])
            print(movie_reviews[id]['localized_title'] + ' ' + str(movie_reviews[id]['rating']))
        if len(movies) == 10:
            break
    print('')
    return movies

def find_movies_with_cast(actor):
    movies = []
    for id in movie_reviews:
        if actor in movie_reviews[id]['cast']:
            movies.append(movie_reviews[id]['localized_title'])
            print(movie_reviews[id]['localized_title'] + ' Actors: ' + ', '.join(movie_reviews[id]['cast']) + '\n')
        if len(movies) == 10:
            break
    return movies

def load_ranker(ranker):
    if ranker == 'bm25':
        return metapy.index.OkapiBM25(k1=1.2,b=0.75,k3=500)
    elif ranker == 'jm':
        return metapy.index.JelinekMercer(0.7)
    elif ranker == 'dp':
        return metapy.index.DirichletPrior(2000)
    else:
        return -1

def run(cfg, ranker_input, query_string):
    # build indexes
    if os.path.exists(os.getcwd() + '\idx'):
        shutil.rmtree(os.getcwd() + '\idx')
    idx = metapy.index.make_inverted_index(cfg)
    # load ranker
    ranker = load_ranker(ranker_input)
    if ranker == -1:
        print('ranker is not set correctly')
        return
    # we don't have IR feedbacks so skip
    # ev = metapy.index.IREval(cfg)

    # how many results do you want, start the timer
    start_time = time.time()
    top_k = 10

    # get the config dictionary
    with open(cfg, 'r') as fin:
        cfg_d = pytoml.load(fin)

    # grab the query runner
    # in our case, we don't need a runner, however in the future there might be usage
    # where we need to runs multiple queries
    query_cfg = cfg_d['query-runner']
    if query_cfg is None:
        print("query-runner table needed in {}".format(cfg))
        return

    # start timer + how many top results do you want
    start_time = time.time()
    top_k = 10


    query = metapy.index.Document()
    ranked_all_relevants = None
    query.content(query_string.strip().lower())
    results = ranker.score(idx, query, top_k)
    ranked_all_relevants = results
    print('Relevant movies (ranked): {} for the query: "{}"'.format(results, query.content()))
    print("Elapsed: {} seconds".format(round(time.time() - start_time, 4)))

    all_ids = []
    with open('movies_ids.dat') as movies_ids_file:
        for line in movies_ids_file:
            all_ids.append(line.strip())
            # print(line.strip())  

    # return all relevant movies
    # note that the id in ranked_all_relevants are 0-indexed
    # so 380 -> will go to line 381 in movies_ids file to get that id, which is the correct behavior
    all_rev_movie_ids = []
    for ranked_all_relevant in ranked_all_relevants:
        all_rev_movie_ids.append(all_ids[ranked_all_relevant[0]])
    print('all relevant movies ids ranked are ' + ' '.join(all_rev_movie_ids))
    print(all_rev_movie_ids)
    return all_rev_movie_ids

if __name__ == '__main__':
    # demos
    find_movies_with_year(1999)
    find_movies_with_gte_rating(4.5)
    find_movies_with_cast('Victor Lipari')

    # check if correct command line is used
    if len(sys.argv) != 4:
        print("Usage: {} config.toml your_ranker query_string".format(sys.argv[0]))
        sys.exit(1)

    # get the config arg
    # should be "config.toml" or "config_whole.toml"
    cfg = sys.argv[1]
    # ranker
    # should be "bm25" or "jm" or "dp"
    ranker = sys.argv[2]
    # query_string
    # can be any string
    query_string = sys.argv[3]
    
    run(cfg, ranker, query_string)