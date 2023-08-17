# -*- coding: utf-8 -*-
"""HW4-nlp-task2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-4dcfgPm4l1m4DNTAJMOfIfi9y30mHW_
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import numpy as np
import csv
import time
import json
import torch.nn.init as init
import os
import shutil
import pandas as pd
import itertools
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

resume = True
directory = os.getcwd()
os.makedirs(os.path.join(directory, "checkpoints"), exist_ok=True)

# Define hyperparameters
EMBEDDING_DIM = 100
HIDDEN_DIM = 256
OUTPUT_DIM = 128
DROPOUT = 0.33
LEARNING_RATE = 1
EPOCHS = 30
BATCH_SIZE = 64

word_vocab = dict()
tag_vocab = dict()
tag_freq = dict()
word_freq = dict()
lower_case_words = []
upper_case_words = []

directory = os.getcwd()
url_train = os.path.join(directory, "data/train")
url_dev = os.path.join(directory, "data/dev")
url_test = os.path.join(directory, "data/test")

word_vocab['<pad>'] = -1
word_vocab['<unk>'] = 0
tag_vocab['<pad>'] = -1

word_counter = 2
tag_counter = 0

with open(url_train, "r", encoding="utf8") as train_file:
    train_reader = csv.reader(train_file, delimiter="\t")

    sent = []
    sent_words = []
    sent_tags = []
    train_set_combined = []
    train_set_words = []
    train_set_tags = []

    for row in train_reader:
        if row == []:
            train_set_combined.append(sent)
            train_set_words.append(sent_words)
            train_set_tags.append(sent_tags)
            sent = []
            sent_words = []
            sent_tags = []
        else:
            (index, word_type, ner_tag) = row[0].split(' ')

            sent.append((word_type, ner_tag))
            sent_words.append(word_type)
            sent_tags.append(ner_tag)

            if (word_type.lower() not in upper_case_words):
                for char in word_type:
                    if char.isupper():
                        upper_case_words.append(word_type.lower())
                        break
        
            if (word_type.lower() not in upper_case_words) and (word_type.lower() not in lower_case_words):
                lower_case_words.append(word_type)
            
            if word_type not in word_vocab:
                word_vocab[word_type] = word_counter
                word_counter += 1

            if ner_tag not in tag_freq:
                tag_freq[ner_tag] = 1
            else:
                tag_freq[ner_tag] += 1
            
            if word_type not in word_freq:
                word_freq[word_type] = 1
            else:
                word_freq[word_type] += 1

    train_set_combined.append(sent)
    train_set_words.append(sent_words)
    train_set_tags.append(sent_tags)

for indx1, sent in enumerate(train_set_words):
    for indx2, word in enumerate(sent):
        if word_freq[word] < 3:
            train_set_words[indx1][indx2] = '<unk>'

import numpy as np

word_to_vec = {}
with open(os.path.join(directory, "glove.6B.100d"), 'r') as f:
    for line in f:
        parts = line.split()
        word = parts[0]
        vec = np.array(parts[1:], dtype=np.float32)
        word_to_vec[word] = vec

# Define embedding matrix
embedding_dim = 100
num_words = len(word_vocab)
embedding_matrix = np.zeros((num_words, EMBEDDING_DIM))
for word, i in word_vocab.items():
    if word.lower() in word_to_vec:
        embedding_matrix[i] = word_to_vec[word.lower()]
    else:
        embedding_matrix[i] = np.random.normal(scale=0.6, size=(embedding_dim,))

idx2word = {i: word for word, i in word_vocab.items()}

word_counter_dev = 0
tag_counter_dev = 0

with open(url_dev, "r", encoding="utf8") as dev_file:
    dev_reader = csv.reader(dev_file, delimiter="\t")

    sent_dev = []
    sent_words_dev = []
    sent_tags_dev = []
    dev_set_combined = []
    dev_set_words = []
    dev_set_tags = []

    for row in dev_reader:
        if row == []:
            dev_set_combined.append(sent_dev)
            dev_set_words.append(sent_words_dev)
            dev_set_tags.append(sent_tags_dev)
            sent_dev = []
            sent_words_dev = []
            sent_tags_dev = []
        else:

            (index, word_type, ner_tag) = row[0].split(' ')
            # print(index, word_type, ner_tag)

            sent_dev.append((word_type, ner_tag))
            sent_words_dev.append(word_type)
            sent_tags_dev.append(ner_tag)

    dev_set_combined.append(sent_dev)
    dev_set_words.append(sent_words_dev)
    dev_set_tags.append(sent_tags_dev)

with open(url_test, "r", encoding="utf8") as test_file:
    test_reader = csv.reader(test_file, delimiter="\t")

    sent_words_test = []
    test_set_words = []

    for row in test_reader:
        if row == []:
            test_set_words.append(sent_words_test)
            sent_words_test = []
        else:

            (index, word_type) = row[0].split(' ')
            sent_words_test.append(word_type)

    test_set_words.append(sent_words_test)
    
vocab_size = len(word_vocab) # number of unique words in the dataset
seq_lengths = torch.LongTensor(list(map(len, train_set_words)))

tag_vocab = {'<pad>': -1,
 'B-ORG': 0,
 'O': 1,
 'B-MISC': 2,
 'B-PER': 3,
 'I-PER': 4,
 'B-LOC': 5,
 'I-ORG': 6,
 'I-MISC': 7,
 'I-LOC': 8}

idx2tag = {i: tag for tag, i in tag_vocab.items()}

class LoadDataset(Dataset):
    def __init__(self, word_data, tag_data):
        self.words = word_data
        self.tags = tag_data

    def convert_to_vector(self, sentence):
        vec = []
        for word in sentence:
            if word in word_vocab:
                vec.append(word_vocab[word])
            else:
                vec.append(word_vocab['<unk>'])
     
        return torch.tensor(vec)

    def convert_tags_to_vector(self, tags):
        vec = []
        for tag in tags:
            if tag in tag_vocab:
                vec.append(tag_vocab[tag])
            else:
                raise Exception('Tag not in vocab')

        return torch.tensor(vec)

    def __len__(self):
        return len(self.words)

    def __getitem__(self, index):
        sentence = self.words[index]
        sentence_vector = self.convert_to_vector(sentence)
        label_vector = self.convert_tags_to_vector(self.tags[index])
        return sentence_vector, label_vector, len(sentence)

class TestLoadDataset(Dataset):
    def __init__(self, word_data):
        self.words = word_data

    def convert_to_vector(self, sentence):
        vec = []
        for word in sentence:
            if word in word_vocab:
                vec.append(word_vocab[word])
            else:
                vec.append(word_vocab['<unk>'])
     
        return torch.tensor(vec)

    def __len__(self):
        return len(self.words)

    def __getitem__(self, index):
        sentence = self.words[index]
        sentence_vector = self.convert_to_vector(sentence)
        return sentence_vector, len(sentence)

def collate_fn(data):
    # vec, labels, lengths = zip(*data)
    vec = torch.nn.utils.rnn.pad_sequence([x[0] for x in data], batch_first=True)
    labels = torch.nn.utils.rnn.pad_sequence([x[1] for x in data], batch_first=True, padding_value= -1)
    return vec, labels, [x[2] for x in data]

def collate_fn_test(data):
    vec = torch.nn.utils.rnn.pad_sequence([x[0] for x in data], batch_first=True)
    return vec, [x[1] for x in data]

# Load data and convert into dataloader - which combines a dataset and a sampler, and provides an iterable over the given dataset.
training_data = LoadDataset(train_set_words, train_set_tags)
dev_data = LoadDataset(dev_set_words, dev_set_tags)

test_data = TestLoadDataset(test_set_words)

train_loader = DataLoader(training_data, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
dev_loader = DataLoader(dev_data, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)

test_loader = DataLoader(test_data, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn_test)

class BLSTM(nn.Module):
    def __init__(self, embedding_dim, hidden_dim, output_dim, dropout):
        super(BLSTM, self).__init__()
        self.num_layers = 1
        self.hidden_dim = hidden_dim
        self.word_to_embedding = word_to_vec
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.embedding.weight.data.copy_(torch.tensor(embedding_matrix))
        self.embedding2 = nn.Embedding(num_embeddings=2, embedding_dim=5)
        self.lstm = nn.LSTM(input_size=105, hidden_size=hidden_dim, bidirectional=True, batch_first=True)
        self.fc1 = nn.Linear(hidden_dim*2, output_dim)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.ELU()
        self.fc2 = nn.Linear(output_dim, 9)

    def forward(self, x, hidden,cells, lengths, indicator):

        embedded = torch.cat((self.embedding(x), self.embedding2(indicator.int())), dim = 2).to(device)

        embedded = torch.nn.utils.rnn.pack_padded_sequence(embedded, lengths, batch_first=True, enforce_sorted=False)

        lstm_out, _ = self.lstm(embedded, (hidden, cells))
        lstm_out, _ = torch.nn.utils.rnn.pad_packed_sequence(lstm_out, batch_first=True)
        out = self.dropout(lstm_out)
        out = self.fc1(out)
        out = self.activation(out)
        out = self.fc2(out)
        return out

    def initHidden(self,batch_size):
        return torch.zeros(2*self.num_layers,batch_size,self.hidden_dim)

    def initCellStates(self,batch_size):
        return torch.zeros(2*self.num_layers,batch_size,self.hidden_dim)

total = sum(tag_freq.values())

vc = [num/total for num in tag_freq.values()]

class_weights = [sum(vc)/v for v in vc]

sum_class_weights = sum(class_weights)

final_class_weights = [cw/sum_class_weights for cw in class_weights]

def save_checkpoint(state, is_best, fdir):
    filepath = os.path.join(fdir, os.path.join(directory, "checkpoints_v7_task2.pt"))
    torch.save(state, filepath)
    if is_best:
        shutil.copyfile(filepath, os.path.join(fdir, os.path.join(directory, "model_v7_task2.pt.tar")))

def load_ckp(checkpoint_fpath, model):
    checkpoint = torch.load(checkpoint_fpath)
    model.load_state_dict(checkpoint['state_dict'])
    best_acc = checkpoint['best_acc']
    return model, checkpoint['epoch'], best_acc

model = BLSTM(EMBEDDING_DIM, HIDDEN_DIM, OUTPUT_DIM, DROPOUT).to(device)
optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE)

if resume:
    model, start_epoch, best_acc = load_ckp(os.path.join(directory, "blstm2.pt"), model)
else:
    start_epoch = 0

# optimizer = optim.SGD(model.parameters(), lr=LEARNING_RATE)

class_weights = torch.FloatTensor(final_class_weights).to(device)
criterion = nn.CrossEntropyLoss(ignore_index=-1).to(device)
# scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 20, gamma=0.1, last_epoch=-1, verbose=False)
best_acc = 0

def capitalization_indicator(X_batch):
    indicator = torch.zeros(X_batch.shape[0], X_batch.shape[1]).to(device)
    for i in range(X_batch.shape[0]):
        for j in range(X_batch.shape[1]):
            word = idx2word[X_batch[i][j].item()].lower()
            if word in word_to_vec:
                if word in upper_case_words:
                    indicator[i][j] = 1
                elif word in lower_case_words:
                    indicator[i][j] = 0
            else:
                indicator[i][j] = 0
    return indicator

for epoch in range(start_epoch, EPOCHS):
    
    train_loss = 0.0
    print(epoch)
    true_labels = []
    predicted_labels = []
    correct = 0

    model.train()

    hidden = model.initHidden(BATCH_SIZE).to(device)
    cells = model.initCellStates(BATCH_SIZE).to(device)

    for indx, (X_batch, y_batch, lengths) in enumerate(train_loader):
        X_batch,y_batch= X_batch.to(device).squeeze(1),y_batch.to(device)
        
        optimizer.zero_grad()
        outputs = model(X_batch, hidden, cells, lengths, capitalization_indicator(X_batch)).to(device)
        outputs = torch.permute(outputs, (0,2,1))
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
    
        train_loss += loss.item()*X_batch.size(0)

        for k in range(len(lengths)):
            correct += np.count_nonzero((outputs.argmax(dim=1)[k][:lengths[k]] == y_batch[k][:lengths[k]]).cpu())

        is_best = (correct/seq_lengths.sum().item()) > best_acc
        best_acc = max((correct/seq_lengths.sum().item()),best_acc)

        save_checkpoint({
            'epoch': epoch + 1,
            'state_dict': model.state_dict(),
            'best_acc': best_acc
        }, is_best, '')
    # scheduler.step()
    train_accuracy = correct/seq_lengths.sum().item()
    train_loss = train_loss/len(train_loader.dataset)
    print('Epoch: {} \t Training Accuracy: {:.6f} \t Training Loss: {:.6f} \t Learning rate: {:.6f} \t'.format(
        # print('Epoch: {} \t Training Loss: {:.6f} \t'.format(
            epoch+1, 
            train_accuracy,
            train_loss,
            optimizer.param_groups[0]['lr']
            ))

correct_dev = 0
predicted_labels = []
true_labels = []
# Testing loop

model = BLSTM(EMBEDDING_DIM, HIDDEN_DIM, OUTPUT_DIM, DROPOUT).to(device)
criterion = nn.CrossEntropyLoss(ignore_index=-1).to(device)

checkpoints = torch.load(os.path.join(directory, "blstm2.pt"))
model.load_state_dict(checkpoints['state_dict'])

model.eval()

def capitalization_indicator(X_batch):
    indicator = torch.zeros(X_batch.shape[0], X_batch.shape[1]).to(device)
    for i in range(X_batch.shape[0]):
        for j in range(X_batch.shape[1]):
            word = idx2word[X_batch[i][j].item()].lower()
            if word in word_to_vec:
                if word in upper_case_words:
                    indicator[i][j] = 1
                elif word in lower_case_words:
                    indicator[i][j] = 0
            else:
                indicator[i][j] = 0
    return indicator

with torch.no_grad():
    test_loss = 0
    for X_batch, y_batch, lengths in dev_loader:
        X_batch,y_batch=X_batch.to(device).squeeze(1) ,y_batch.to(device)
        hidden = model.initHidden(BATCH_SIZE).to(device)
        cells = model.initCellStates(BATCH_SIZE).to(device)
        outputs = model(X_batch, hidden,cells, lengths, capitalization_indicator(X_batch)).to(device)
        outputs = outputs.permute(0, 2, 1)
        test_loss = criterion(outputs, y_batch)
        for k in range(len(lengths)):
            # correct_dev += np.count_nonzero(outputs.argmax(dim=1)[k][:lengths[k]] == y_batch[k][:lengths[k]])
            correct_dev += np.count_nonzero((outputs.argmax(dim=1)[k][:lengths[k]] == y_batch[k][:lengths[k]]).cpu())
        
        for i in range(len(outputs)):
            predicted_labels.append(outputs.argmax(dim=1)[i][:lengths[i]].tolist())
            true_labels.append(y_batch[i][:lengths[i]].tolist())

seq_lengths_dev = torch.LongTensor(list(map(len, dev_set_words)))
print("Accuracy: ", correct_dev/seq_lengths_dev.sum().item())

flattened_list_pred = list(itertools.chain.from_iterable(predicted_labels))
flattened_list_true_lab = list(itertools.chain.from_iterable(true_labels))

from sklearn import metrics

precision = metrics.precision_score(flattened_list_true_lab, flattened_list_pred, average='weighted')
recall = metrics.recall_score(flattened_list_true_lab, flattened_list_pred, average='weighted')
F1_score = 2 * (precision * recall) / (precision + recall)

precision

recall

F1_score

testing_list = []
k = 0

for i in range(len(dev_set_combined)):
    for j in range(len(dev_set_combined[i])):
        # print(dev_set_combined[i][j][0])
        testing_list.append( [ str(j+1) + ' ' + dev_set_combined[i][j][0] + ' ' + idx2tag[flattened_list_pred[k]] ] )
        # testing_list.append( [ str(j+1) + ' ' + dev_set_combined[i][j][0] + ' ' + dev_set_combined[i][j][1] + ' ' + idx2tag[flattened_list_pred[k]] ] )
        k += 1
    testing_list.append(' ')

with open("dev2.out", "w") as file:
    for element in testing_list:
        file.write(element[0] + "\n")

# !perl conll03eval.txt < dev2.txt





correct_test = 0
predicted_labels = []

model = BLSTM(EMBEDDING_DIM, HIDDEN_DIM, OUTPUT_DIM, DROPOUT).to(device)
criterion = nn.CrossEntropyLoss(ignore_index=-1).to(device)

checkpoints = torch.load(os.path.join(directory, "blstm2.pt"))

# print(checkpoints['state_dict']['embedding.weight'][0]))
model.load_state_dict(checkpoints['state_dict'])

# Testing loop
model.eval()
with torch.no_grad():
    test_loss = 0
    for X_batch, lengths in test_loader:
        X_batch=X_batch.to(device).squeeze(1)
        hidden = model.initHidden(BATCH_SIZE).to(device)
        cells = model.initCellStates(BATCH_SIZE).to(device)
        outputs = model(X_batch, hidden,cells, lengths, capitalization_indicator(X_batch)).to(device)
        outputs = outputs.permute(0, 2, 1)
        
        for i in range(len(outputs)):
            predicted_labels.append(outputs.argmax(dim=1)[i][:lengths[i]].tolist())

flattened_list_pred_test = list(itertools.chain.from_iterable(predicted_labels))

testing_list_test = []
k = 0

for i in range(len(test_set_words)):
    for j in range(len(test_set_words[i])):
        testing_list_test.append( [ str(j+1) + ' ' + test_set_words[i][j] + ' ' + idx2tag[flattened_list_pred_test[k]] ] )
        k += 1
    testing_list_test.append(' ')

with open("test2.out", "w") as file:
    for element in testing_list_test:
        file.write(element[0] + "\n")
