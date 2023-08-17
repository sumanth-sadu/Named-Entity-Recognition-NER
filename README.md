# Named-Entity-Recognition-NER
Hands-on experience on building deep learning models on named entity recognition (NER)

To know the problem statement or description of the assignment: CSCI544_2023_HW4.pdf
For results and explanation: HW4-NLP-Report.pdf
code files: Named-Entity-Recognition-NER/code/..
checkpoints to generate the results mentioned in HW4-NLP-Report.pdf: Named-Entity-Recognition-NER/outputs/checkpoints/..
outputs expected: Named-Entity-Recognition-NER/outputs/..
data: Named-Entity-Recognition-NER/data/..

Note:

1. Provided two .py files for task 1 and task 2, respectively, which include code for training and testing on both dev and test sets. 
2. hw4_nlp_task1.py generates dev1.out and test1.out, while hw4_nlp_task2.py produces dev2.out and test2.out files.
3. To run either of the .py files, use the command "python {filename}.py".
4. Both files must be run on a GPU.
5. The data folder, which contains the train, test, and dev sets, must be located in the same directory as the .py files.
6. If blstm1.pt or blstm2.pt checkpoints are used, it is recommended to have both in the same directory as the .py files. When the training code is executed in both files, the output is saved to a new .pt checkpoint file named checkpoint_v7.pt and checkpoint_v7_task2.pt.
