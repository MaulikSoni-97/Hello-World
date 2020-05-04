import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from Utils import matrix_mul1, matrix_mul2,element_wise_mul
import pandas as pd
import numpy as np
import csv

class WordAttNet(nn.Module):
    '''
    This class will help in getting features at tokens level
    '''
    def __init__(self, word2vec_path,num_classes=8,hidden_size=50):
        super(WordAttNet, self).__init__()
        dict = pd.read_csv(filepath_or_buffer=word2vec_path, header=None, sep=" ", quoting=csv.QUOTE_NONE).values[:, 1:]
        dict_len, embed_size = dict.shape
        dict_len += 1
        unknown_word = np.zeros((1, embed_size))
        dict = torch.from_numpy(np.concatenate([unknown_word, dict], axis=0).astype(np.float))
        self.word_weight = nn.Parameter(torch.Tensor(2 * hidden_size, 2 * hidden_size))
        self.word_bias = nn.Parameter(torch.Tensor(1, 2 * hidden_size))
        self.context_weight = nn.Parameter(torch.Tensor(2 * hidden_size, 1))
        self.lookup = nn.Embedding(num_embeddings=dict_len, embedding_dim=embed_size).from_pretrained(dict)
        self.gru = nn.GRU(embed_size, hidden_size,bidirectional=True)
        self.fc = nn.Linear(2 * hidden_size,num_classes)
        # or we can use
        # self.lookup=nn.Embedding(num_embeddings=dict_len, embedding_dim=embed_size)
        # self.lookup.weight.data.copy_(torch.from_numpy(dict)) #caution:check out line 8 as already in torch format

        self._create_weights(mean=0.0, std=1)

    def _create_weights(self, mean=0.0, std=1):

        self.word_weight.data.normal_(mean, std)
        self.context_weight.data.normal_(mean, std)

    def forward(self, input, hidden_state):

        output = self.lookup(input)
        #gru layer
        f_output, h_output = self.gru(output.float(), hidden_state)  # feature output and hidden state output
        output = matrix_mul1(f_output, self.word_weight, self.word_bias)
        output = matrix_mul2(output, self.context_weight,False)

        # softmax output
        output = F.softmax(output,dim=1)
        output = element_wise_mul(f_output,output.permute(1,0))
        output = output.squeeze(0)

        # last fully connected layer which results in (1,8) shape vector
        output = self.fc(output)
        
        return output, h_output