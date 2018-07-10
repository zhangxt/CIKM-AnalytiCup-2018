import sys
sys.path.append('../')

import os
import pickle
import copy
import numpy as np
from tqdm import tqdm


from Config import config
from Config import tool
from Preprocessing.Tokenizer import *
from Preprocessing.WordDict import *


class Preprocess():
    def __init__(self):
        self.max_length = 50
        self.tokenizer = Tokenizer()

    def load_train_data(self, tag='en'):
        print("导入训练数据")
        if tag == 'en':
            path = config.TOKEN_TRAIN
        elif tag == 'es':
            path = config.TOKEN_VAL

        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        if tag == 'en':
            data_path = config.EN_TRAIN_FILE
        elif tag == 'es':
            data_path = config.ES_TRAIN_FILE

        en_sentence_left = []
        en_sentence_right = []
        es_sentence_left = []
        es_sentence_right = []
        labels = []

        with open(data_path, 'r', encoding='utf-8') as fr:
            lines = fr.readlines()
            for line in tqdm(lines):
                lineList = line.split('\t')
                assert len(lineList) == 5
                # 句子切分
                if tag == 'en':
                    # 英文
                    tmp_en_left = self.tokenizer.en_str_clean(lineList[0])
                    tmp_en_right = self.tokenizer.en_str_clean(lineList[2])

                    # 西班牙文
                    tmp_es_left = self.tokenizer.es_str_clean(lineList[1])
                    tmp_es_right = self.tokenizer.es_str_clean(lineList[3])

                elif tag == 'es':
                    tmp_en_left = self.tokenizer.en_str_clean(lineList[1])
                    tmp_en_right = self.tokenizer.en_str_clean(lineList[3])

                    tmp_es_left = self.tokenizer.es_str_clean(lineList[0])
                    tmp_es_right = self.tokenizer.es_str_clean(lineList[2])

                # 先不要加trick
                # 添加公共序列
                # en_common_list = tool.LCS(tmp_en_left, tmp_en_right)
                # tmp_en_left.extend(en_common_list)
                # tmp_en_right.extend(en_common_list)
                #
                # es_common_list = tool.LCS(tmp_es_left, tmp_es_right)
                # tmp_es_left.extend(es_common_list)
                # tmp_es_right.extend(es_common_list)

                en_sentence_left.append(tmp_en_left)
                en_sentence_right.append(tmp_en_right)
                es_sentence_left.append(tmp_es_left)
                es_sentence_right.append(tmp_es_right)

                labels.append(int(lineList[4]))

        with open(path, 'wb') as pkl:
            pickle.dump((en_sentence_left, en_sentence_right, es_sentence_left, es_sentence_right, labels), pkl)

        return (en_sentence_left, en_sentence_right, es_sentence_left, es_sentence_right, labels)


    def load_test(self):
        print("导入测试数据")

        path = config.TOKEN_TEST
        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        sentence_left = []
        sentence_right = []

        with open(config.TEST_FiLE, 'r', encoding='utf-8') as fr:
            lines = fr.readlines()

            for line in lines:
                lineList = line.split('\t')
                tmp_left = self.tokenizer.es_str_clean(lineList[0])
                tmp_right = self.tokenizer.es_str_clean(lineList[1])

                # common_list = tool.LCS(tmp_left, tmp_right)
                # tmp_left.extend(common_list)
                # tmp_right.extend(common_list)

                sentence_left.append(tmp_left)
                sentence_right.append(tmp_right)

        with open(path, 'wb') as pkl:
            pickle.dump((sentence_left, sentence_right), pkl)

        return (sentence_left, sentence_right)


    def es2index(self, tag='es'):
        print("建立词到索引的字典")
        word2index = WordDict()
        path = config.cache_prefix_path + 'Es2IndexDic.pkl'
        if os.path.exists(path):
            return word2index.loadWord2IndexDic(tag)

        _, _, train_left, train_right, _  = self.load_train_data('en')
        _, _, dev_left, dev_right, _ = self.load_train_data('es')
        test_left, test_right = self.load_test()

        for i in range(len(train_left)):
            for word in train_left[i]:
                word2index.add_word(word, tag)
            for word in train_right[i]:
                word2index.add_word(word, tag)

        for i in range(len(dev_left)):
            for word in dev_left[i]:
                word2index.add_word(word, tag)
            for word in dev_right[i]:
                word2index.add_word(word, tag)

        for i in range(len(test_left)):
            for word in test_left[i]:
                word2index.add_word(word, tag)
            for word in test_right[i]:
                word2index.add_word(word, tag)

        word2index.saveWord2IndexDic(tag)
        return word2index.Es2IndexDic


    def get_es_index_data(self, tag):
        print("将语料转化为索引表示")

        if tag == 'train':
            path = config.cache_prefix_path + 'index_train.pkl'
        elif tag == 'dev':
            path = config.cache_prefix_path + 'index_dev.pkl'
        elif tag == 'test':
            path = config.cache_prefix_path + 'index_test.pkl'

        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        dic = {
            'train':'en',
            'dev': 'es'
        }


        if tag == 'train' or tag == 'dev':
            _, _, left_sentence, right_sentence, labels = self.load_train_data(dic[tag])
        if tag == 'test':
            left_sentence, right_sentence = self.load_test()

        word2index = self.es2index()

        left_index = []
        right_index = []

        for i in range(len(left_sentence)):
            left_index.append([word2index.get(word, 1) for word in left_sentence[i]])
            right_index.append([word2index.get(word, 1) for word in right_sentence[i]])

        if tag == 'train' or tag == 'dev':
            with open(path, 'wb') as pkl:
                pickle.dump((left_index, right_index, labels), pkl)
            return (left_index, right_index, labels)

        if tag == 'test':
            with open(path, 'wb') as pkl:
                pickle.dump((left_index, right_index), pkl)
            return (left_index, right_index)

    def get_es_index_padding(self, tag):
        print("padding")
        if tag == 'train':
            path = config.cache_prefix_path + 'train_index_padding.pkl'
        elif tag == 'dev':
            path = config.cache_prefix_path + 'dev_index_padding.pkl'
        elif tag == 'test':
            path = config.cache_prefix_path + 'test_index_padding.pkl'

        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        if tag == 'train' or tag == 'dev':
            left_index, right_index, labels = self.get_es_index_data(tag)
        if tag == 'test':
            left_index, right_index = self.get_es_index_data(tag)

        left_index_padding = copy.deepcopy(left_index)
        right_index_padding = copy.deepcopy(right_index)

        for i in range(len(left_index)):
            if len(left_index[i]) < self.max_length:
                left_index_padding[i] += [0] * (self.max_length - len(left_index_padding[i]))
            else:
                left_index_padding[i] = left_index_padding[i][:self.max_length]

            if len(right_index[i]) < self.max_length:
                right_index_padding[i] += [0] * (self.max_length - len(right_index_padding[i]))
            else:
                right_index_padding[i] = right_index_padding[i][:self.max_length]

        if tag == 'train' or tag == 'dev':
            with open(path, 'wb') as pkl:
                pickle.dump((left_index_padding, right_index_padding, labels), pkl)
            return (left_index_padding, right_index_padding, labels)
        if tag == 'test':
            with open(path, 'wb') as pkl:
                pickle.dump((left_index_padding, right_index_padding), pkl)
            return (left_index_padding, right_index_padding)


    def get_length(self, tag):
        print("get length")
        if tag == 'train':
            path = config.cache_prefix_path + 'train_length.pkl'
        elif tag == 'dev':
            path = config.cache_prefix_path + 'dev_length.pkl'
        elif tag == 'test':
            path = config.cache_prefix_path + 'test_length.pkl'

        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        if tag == 'train':
            _, _, sentence_left, sentence_right, _ = self.load_train_data('en')
        elif tag == 'dev':
            _, _, sentence_left, sentence_right, _ = self.load_train_data('es')
        elif tag == 'test':
            sentence_left, sentence_right = self.load_test()

        left_length = [min(len(sentence), self.max_length) for sentence in sentence_left]
        right_length = [min(len(sentence), self.max_length) for sentence in sentence_right]

        with open(path, 'wb') as pkl:
            pickle.dump((left_length, right_length), pkl)
        return (left_length, right_length)


    def load_translation_data(self):
        print("loading translation data")

        path = config.cache_prefix_path + 'translation_token.pkl'
        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        data_path = config.TRANSLATE_FILE
        es = []
        en = []
        with open(data_path, 'r', encoding='utf-8') as fr:
            lines = fr.readlines()
            for line in tqdm(lines):
                line = line.split("\t")
                es.append(self.tokenizer.es_str_clean(line[0]))
                en.append(self.tokenizer.en_str_clean(line[1]))

        with open(path, 'wb') as pkl:
            pickle.dump((es, en), pkl)
        return (es, en)

    def load_all_data(self):
        print('loading all spanish&english')

        path = config.cache_prefix_path + 'all_token.pkl'
        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        en = []
        es = []

        en_left_train, en_right_train, es_left_train, es_right_train, _ = self.load_train_data('en')
        en_left_dev, en_right_dev, es_left_dev, es_right_dev, _ = self.load_train_data('es')
        es_left_test, es_right_test = self.load_test()
        es_trans, en_trans = self.load_translation_data()

        en.extend(en_left_train)
        en.extend(en_right_train)
        en.extend(en_left_dev)
        en.extend(en_right_dev)
        en.extend(en_trans)

        es.extend(es_left_train)
        es.extend(es_right_train)
        es.extend(es_left_dev)
        es.extend(es_right_dev)
        es.extend(es_left_test)
        es.extend(es_right_test)
        es.extend(es_trans)

        with open(path, 'wb') as pkl:
            pickle.dump((es, en), pkl)
        return es, en

    def swap_data(self, tag1, tag2):
        print('Swapping data')

        if tag1 == 'train':
            if tag2 == 'token':
                path = config.cache_prefix_path + 'train_token_swap.pkl'
            elif tag2 == 'index':
                path = config.cache_prefix_path + 'train_index_swap.pkl'
            elif tag2 == 'padding':
                path = config.cache_prefix_path + 'train_padding_swap.pkl'
        elif tag1 == 'dev':
            if tag2 == 'token':
                path = config.cache_prefix_path + 'dev_token_swap.pkl'
            elif tag2 == 'index':
                path = config.cache_prefix_path + 'dev_index_swap.pkl'
            elif tag2 == 'padding':
                path = config.cache_prefix_path + 'dev_padding_swap.pkl'

        if os.path.exists(path):
            with open(path, 'rb') as pkl:
                return pickle.load(pkl)

        dic = {
            'train':'en',
            'dev': 'es'
        }

        if tag2 == 'token':
            _, _, left, right, labels = self.load_train_data(dic[tag1])
        elif tag2 == 'index':
            left, right, labels = self.get_es_index_data(tag1)
        elif tag2 == 'padding':
            left, right, labels = self.get_es_index_padding(tag1)

        with open(path, 'wb') as pkl:
            pickle.dump((right, left, labels), pkl)

        return (right, left, labels)




if __name__ == '__main__':
    p = Preprocess()

    p.load_train_data('en')
    p.load_train_data('es')
    p.load_test()
    p.es2index()
    p.get_es_index_data('train')
    p.get_es_index_data('dev')
    p.get_es_index_data('test')
    p.get_es_index_padding('train')
    p.get_es_index_padding('dev')
    p.get_es_index_padding('test')
    p.get_length('train')
    p.get_length('dev')
    p.get_length('test')
    p.load_translation_data()
    p.load_all_data()
