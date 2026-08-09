---
license: cc-by-nc-sa-4.0
task_categories:
- text-classification
- summarization
- translation
- token-classification
- feature-extraction
- sentence-similarity
language:
- en
- hi
- bn
- gu
- ml
- mr
- or
- pa
- ta
- te
extra_gated_fields:
  'Full Name': text
  'Affiliation (Organization/University)': text
  'Designation/Status in Your Organization': text
  'Country': country
  'I want to use this dataset for (please provide the reason(s))': text
  'IL-TUR dataset is free for research use but NOT for commercial use; do you agree if you are provided with the IL-TUR dataset, you will NOT use for any commercial purposes? Also do you agree that you will not be sharing this dataset further or uploading it anywhere else on the internet': checkbox
  'DISCLAIMER The dataset is released for research purposes only and authors do not take any responsibility for any damage or loss arising due to usage of data or any system/model developed using the dataset': checkbox 
tags:
- legal
- indian law
- benchmark
- legal ner
- rhetorical role
- judgment prediction
- judgment explanation
- bail
- legal statute
- prior case
- summarization
- machine translation
size_categories:
- 10K<n<100K
pretty_name: IL-TUR
config_names:
- lner
- rr
- cjpe
- bail
- lsi
- pcr
- summ
- lmt
dataset_info:
- config_name: lner
  features:
  - name: id
    dtype: string
  - name: text
    dtype: string
  - name: spans
    list:
      struct:
      - name: start
        dtype: int64
      - name: end
        dtype: int64
      - name: label
        class_label:
          names:
            '0': APP
            '1': RESP
            '2': A.COUNSEL
            '3': R.COUNSEL
            '4': JUDGE
            '5': WIT
            '6': AUTH
            '7': COURT
            '8': STAT
            '9': PREC
            '10': DATE
            '11': CASENO
  splits:
  - name: fold_1
    num_examples: 35
  - name: fold_2
    num_examples: 35
  - name: fold_3
    num_examples: 35
- config_name: rr
  features:
  - name: id
    dtype: string
  - name: text
    list: string
  - name: labels
    list:
      class_label:
        names:
          '0': Fact
          '1': Issue
          '2': ArgumentPetitioner
          '3': ArgumentRespondent
          '4': Statute
          '5': Dissent
          '6': PrecedentReliedUpon
          '7': PrecedentNotReliedUpon
          '8': PrecedentOverruled
          '9': RulingByLowerCourt
          '10': RatioOfTheDecision
          '11': RulingByPresentCourt
          '12': None
  - name: expert_1
    struct:
    - name: primary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: secondary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: tertiary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: overall
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
  - name: expert_2
    struct:
    - name: primary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: secondary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: tertiary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: overall
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
  - name: expert_3
    struct:
    - name: primary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: secondary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: tertiary
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
    - name: overall
      list:
        class_label:
          names:
            '0': Fact
            '1': Issue
            '2': ArgumentPetitioner
            '3': ArgumentRespondent
            '4': Statute
            '5': Dissent
            '6': PrecedentReliedUpon
            '7': PrecedentNotReliedUpon
            '8': PrecedentOverruled
            '9': RulingByLowerCourt
            '10': RatioOfTheDecision
            '11': RulingByPresentCourt
            '12': None
  splits:
  - name: CL_train
    num_examples: 40
  - name: CL_dev
    num_examples: 5
  - name: CL_test
    num_examples: 5
  - name: IT_train
    num_examples: 40
  - name: IT_dev
    num_examples: 5
  - name: IT_test
    num_examples: 5
- config_name: cjpe
  features:
  - name: id
    dtype: string
  - name: text
    dtype: string
  - name: label
    dtype:
      class_label:
        names:
          '0': REJECTED
          '1': ACCEPTED
  - name: expert_1
    struct:
    - name: label
      dtype:
        class_label:
          names:
            '0': REJECTED
            '1': ACCEPTED
    - name: rank1
      list: string
    - name: rank2
      list: string
    - name: rank3
      list: string
    - name: rank4
      list: string
    - name: rank5
      list: string
  - name: expert_2
    struct:
    - name: label
      dtype:
        class_label:
          names:
            '0': REJECTED
            '1': ACCEPTED
    - name: rank1
      list: string
    - name: rank2
      list: string
    - name: rank3
      list: string
    - name: rank4
      list: string
    - name: rank5
      list: string
  - name: expert_3
    struct:
    - name: label
      dtype:
        class_label:
          names:
            '0': REJECTED
            '1': ACCEPTED
    - name: rank1
      list: string
    - name: rank2
      list: string
    - name: rank3
      list: string
    - name: rank4
      list: string
    - name: rank5
      list: string
  - name: expert_4
    struct:
    - name: label
      dtype:
        class_label:
          names:
            '0': REJECTED
            '1': ACCEPTED
    - name: rank1
      list: string
    - name: rank2
      list: string
    - name: rank3
      list: string
    - name: rank4
      list: string
    - name: rank5
      list: string
  - name: expert_5
    struct:
    - name: label
      dtype:
        class_label:
          names:
            '0': REJECTED
            '1': ACCEPTED
    - name: rank1
      list: string
    - name: rank2
      list: string
    - name: rank3
      list: string
    - name: rank4
      list: string
    - name: rank5
      list: string
  splits:
  - name: expert
    num_examples: 56
  - name: single_train
    num_examples: 5082
  - name: single_dev
    num_examples: 2511
  - name: multi_train
    num_examples: 32305
  - name: multi_dev
    num_examples: 994
  - name: test
    num_examples: 1517
- config_name: bail
  features:
  - name: id
    dtype: string
  - name: district
    dtype: string
  - name: text
    struct:
    - name: facts-and-arguments
      list: string
    - name: judge-opinion
      list: string
  - name: label
    dtype:
      class_label:
        names:
          '0': DENIED
          '1': GRANTED
  splits:
  - name: train_all
    num_examples: 123742
  - name: dev_all
    num_examples: 17707
  - name: test_all
    num_examples: 35400
  - name: train_specific
    num_examples: 124341
  - name: dev_specific
    num_examples: 15929
  - name: test_specific
    num_examples: 36579
- config_name: lsi
  features:
  - name: id
    dtype: string
  - name: text
    list: string
  - name: labels
    list:
      class_label:
        names:
          '0': Section 2
          '1': Section 3
          '2': Section 4
          '3': Section 5
          '4': Section 13
          '5': Section 34
          '6': Section 107
          '7': Section 109
          '8': Section 114
          '9': Section 120
          '10': Section 120B
          '11': Section 143
          '12': Section 147
          '13': Section 148
          '14': Section 149
          '15': Section 155
          '16': Section 156
          '17': Section 161
          '18': Section 164
          '19': Section 173
          '20': Section 174A
          '21': Section 186
          '22': Section 188
          '23': Section 190
          '24': Section 193
          '25': Section 200
          '26': Section 201
          '27': Section 228
          '28': Section 229A
          '29': Section 279
          '30': Section 294
          '31': Section 294(b)
          '32': Section 299
          '33': Section 300
          '34': Section 302
          '35': Section 304
          '36': Section 304A
          '37': Section 304B
          '38': Section 306
          '39': Section 307
          '40': Section 308
          '41': Section 313
          '42': Section 320
          '43': Section 323
          '44': Section 324
          '45': Section 325
          '46': Section 326
          '47': Section 332
          '48': Section 336
          '49': Section 337
          '50': Section 338
          '51': Section 341
          '52': Section 342
          '53': Section 353
          '54': Section 354
          '55': Section 363
          '56': Section 364
          '57': Section 365
          '58': Section 366
          '59': Section 366A
          '60': Section 375
          '61': Section 376
          '62': Section 376(2)
          '63': Section 379
          '64': Section 380
          '65': Section 384
          '66': Section 389
          '67': Section 392
          '68': Section 394
          '69': Section 395
          '70': Section 397
          '71': Section 406
          '72': Section 409
          '73': Section 411
          '74': Section 415
          '75': Section 417
          '76': Section 419
          '77': Section 420
          '78': Section 427
          '79': Section 436
          '80': Section 437
          '81': Section 438
          '82': Section 447
          '83': Section 448
          '84': Section 450
          '85': Section 452
          '86': Section 457
          '87': Section 465
          '88': Section 467
          '89': Section 468
          '90': Section 471
          '91': Section 482
          '92': Section 494
          '93': Section 498
          '94': Section 498A
          '95': Section 500
          '96': Section 504
          '97': Section 506
          '98': Section 509
          '99': Section 511
  splits:
  - name: train
    num_examples: 42750
  - name: dev
    num_examples: 10181
  - name: test
    num_examples: 13019
  - name: statutes
    num_examples: 100
- config_name: pcr
  features:
  - name: id
    dtype: string
  - name: text
    list: string
  - name: relevant_candidates
    list: string
  splits:
  - name: train_candidates
    num_examples: 4320
  - name: dev_candidates
    num_examples: 1023
  - name: test_candidates
    num_examples: 1727
  - name: train_queries
    num_examples: 827
  - name: dev_queries
    num_examples: 118
  - name: test_queries
    num_examples: 237
- config_name: summ
  features:
  - name: id
    dtype: string
  - name: document
    list: string
  - name: summary
    list: string
  - name: num_doc_tokens
    dtype: int64
  - name: num_summ_tokens
    dtype: int64
  splits:
  - name: train
    num_examples: 7030
  - name: test
    num_examples: 100
- config_name: lmt
  features:
  - name: id
    dtype: string
  - name: src_lang
    dtype: string
  - name: src
    dtype: string
  - name: tgt_lang
    dtype: string
  - name: tgt
    dtype: string
  splits:
  - name: acts
    num_examples: 4036
  - name: cci_faq
    num_examples: 1460
  - name: ip
    num_examples: 1020
configs:
- config_name: lner
  data_files:
  - split: fold_1
    path: lner/fold_1*
  - split: fold_2
    path: lner/fold_2*
  - split: fold_3
    path: lner/fold_3*
- config_name: rr
  data_files:
  - split: CL_train
    path: rr/CL_train*
  - split: CL_dev
    path: rr/CL_dev*
  - split: CL_test
    path: rr/CL_test*
  - split: IT_train
    path: rr/IT_train*
  - split: IT_dev
    path: rr/IT_dev*
  - split: IT_test
    path: rr/IT_test*
- config_name: cjpe
  data_files:
  - split: expert
    path: cjpe/expert*
  - split: single_train
    path: cjpe/single_train*
  - split: single_dev
    path: cjpe/single_dev*
  - split: multi_train
    path: cjpe/multi_train*
  - split: multi_dev
    path: cjpe/multi_dev*
  - split: test
    path: cjpe/test*
- config_name: bail
  data_files:
  - split: train_all
    path: bail/train_all*
  - split: dev_all
    path: bail/dev_all*
  - split: test_all
    path: bail/test_all*
  - split: train_specific
    path: bail/train_specific*
  - split: dev_specific
    path: bail/dev_specific*
  - split: test_specific
    path: bail/test_specific*
- config_name: lsi
  data_files:
  - split: train
    path: lsi/train*
  - split: dev
    path: lsi/dev*
  - split: test
    path: lsi/test*
  - split: statutes
    path: lsi/statutes*
- config_name: pcr
  data_files:
  - split: train_candidates
    path: pcr/train_candidates*
  - split: dev_candidates
    path: pcr/dev_candidates*
  - split: test_candidates
    path: pcr/test_candidates*
  - split: train_queries
    path: pcr/train_queries*
  - split: dev_queries
    path: pcr/dev_queries*
  - split: test_queries
    path: pcr/test_queries*
- config_name: summ
  data_files:
  - split: train
    path: summ/train*
  - split: test
    path: summ/test*
- config_name: lmt
  data_files:
  - split: acts
    path: lmt/acts*
  - split: cci_faq
    path: lmt/cci_faq*
  - split: ip
    path: lmt/ip*
---

# Dataset Card for "IL-TUR"

## Dataset Description

### Summary
**"IL-TUR": Benchmark for Indian Legal Text Understanding and Reasoning** is a collaborative effort to establish a modern benchmark for training and evaluating AI/NLP models on Indian Law. IL-TUR consists of 8 foundational tasks, requiring different types of understanding and skills. Apart from English, some tasks involve Indic languages.

This dataset repository has been created to unify the data formats of all tasks in a singular style. Users will have the option to both utilize the [Dataset Viewer](https://huggingface.co/datasets/shounakpaul95/Benchmark-Testing2/viewer) to inspect each dataset and data split, as well as use Python commands to download and access the data directly. We hope that this will encourage more researchers to take up these tasks in legal AI, and help them adapt easily.

If you use this dataset (or any task specific dataset) in your research, please cite IL-TUR paper and the paper corresponding to the task-set used:

### Usage
```
  from datasets import load_dataset
  dataset = load_dataset("Exploration-Lab/IL-TUR", "<task_name>", revision="script")
```

## Citation Information
```
@inproceedings{iltur-2024,
      title = "IL-TUR: Benchmark for Indian Legal Text Understanding and Reasoning",
      author = "Joshi, Abhinav and Paul, Shounak and Sharma, Akshat and Goyal, Pawan and Ghosh, Saptarshi and Modi, Ashutosh"
      booktitle = "Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
      month = aug,
      year = "2024",
      address = "Bangkok, Thailand",
      publisher = "Association for Computational Linguistics",
  }
```


## Supported Tasks
The following tasks (and datasets) are part of IL-TUR:

|**Task**|**Dataset**|**Source**|**Language**|**Task Type**|
|:-------|:---------:|:--------:|:-----------|:-----------:|
|L-NER|105 docs|-|en|Sequence Classification|
|RR|21,184 sents|[Malik et al. (2022)](https://aclanthology.org/2022.nllp-1.13)|en|Multi-label Classification|
|CJPE|ILDC|[Malik et al. (2021)](https://aclanthology.org/2021.acl-long.313/)|en|Binary Classification, Extraction|
|BAIL|HLDC|[Kapoor et al. (2022)](https://aclanthology.org/2022.findings-acl.278/)|hi|Binary Classification|
|LSI|ILSI|[Paul et al. (2022)](https://ojs.aaai.org/index.php/AAAI/article/view/21363)|en|Multi-label Classification|
|PCR|IL-PCR|[Joshi et al. (2023)](https://aclanthology.org/2023.acl-long.777/)|en|Retrieval|
|SUMM|In-Abs|[Shukla et al. (2022)](https://aclanthology.org/2022.aacl-main.77/)|en|Generation|
|L-MT|MiLPAC|[Mahapatra et al. (2023)](https://arxiv.org/abs/2310.09765/)|en, hi, bn, gu, mr, ml, or, pa, ta, te|Generation|

---
### L-NER (Legal Named Entity Recognition)

L-NER aims to automatically predict Named Entities (e.g. Judge, Appellant, Respondent, etc.) in a legal document, along with the class. 
Unlike standard NER, legal entities are more fine-grained, e.g., PER can be categorized as JUDGE, APPELLANT, RESPONDENT, etc. 

**Data Source:** The dataset consists of 105 Indian Supreme Court case documents. All documents are annotated with *every* instance of NERs.

**Data Splits:** The data is divided into 3 folds, 'fold_1', 'fold_2' and 'fold_3' each having 35 documents.

**Data Instance:** An example from 'fold_1' looks as follows:
```json
{
  "id": "115651329"
  "text": "REPORTABLE IN THE SUPREME COURT OF INDIA CRIMINAL APPELLATE JURISDICTION CRIMINAL APPEAL NO. 92/2015 JAGE RAM & ORS. ..."
  "spans": [
    {"start": 137, "end": 153, "label": 1},
    {"start": 252, "end": 261, "label": 10}
    ...
  ]
}
```
Instances from all splits have a similar structure.

**Data Fields:**

* 'id': string &rarr; IndianKanoon Case ID
* 'text': string &rarr; Full document text
* 'spans': List(
    * 'start': int &rarr; starting char index
    * 'end': int &rarr; ending char index + 1
    * 'label': class_label &rarr; NER label
  
  )
  
<details>
  <summary>List of NER labels</summary>
  "APP",  "RESP",  "A.COUNSEL",  "R.COUNSEL",  "JUDGE",  "WIT",  "AUTH",  "COURT",  "STAT",  "PREC",  "DATE",  "CASENO"
</details>

---

---
### RR (Rhetorical Role Prediction)

RR aims to segment a legal document into topically coherent units such as Facts, Arguments, Rulings, etc. 
Unlike documents of many countries, Indian court case documents often do not have explicit segmentation or headings, etc., necessiating the automation of this task.

**Data Source:** The dataset was created from 100 cases involving Competition Law and Income Tax from the Indian Supreme Court.

**Data Splits:** The data is divided into  6 splits; 
'CL_train' (40 docs), 'CL_dev' (5 docs) and 'CL_test' (5 docs) for Competition Law, 
'IT_train' (40 docs), 'IT_dev' (5 docs) and 'IT_test' (5 docs) for Income Tax

**Data Instance:** An example from 'fold_1' looks as follows:
```json
{
  "id": "CCI_Confederation_of_Real_Estate_Developers_AssociatioCO201807081816081635COM964576"
  "text": ["The instant matter filed by the Confederation of Real Estate Developers Association of India ...", "In the said order, the Commission had held ...", ...]
  "labels": [0, 9, ...]
  "expert_1": {
    "primary": [0, 9, ...]
    "secondary": [12, 12, ...]
    "tertiary": [12, 12, ...]
    "overall": [0, 9, ...]
  }
  "expert_2": {...}
  "expert_3": {...}
  }
}
```
Instances from all splits have a similar structure.

**Data Fields:**

* 'id': string &rarr; Case ID
* 'text': List(string) &rarr; Full document text divided into sentences
* 'labels': List(class_label) &rarr; Final rhetorical role of each sentence as per majority decision
* 'expert_1':
    * 'primary': List(class_label) &rarr; Primary rhetorical role of each sentence according to expert_1
    * 'secondary': List(class_label) &rarr; Secondary rhetorical role of each sentence according to expert_1
    * 'tertiary': List(class_label) &rarr; Tertiary rhetorical role of each sentence according to expert_1
    * 'overall': List(class_label) &rarr; Final rhetorical role of each sentence according to expert_1
* 'expert_2' &rarr; Similar to expert_1
* 'expert_3' &rarr; Similar to expert_1

  
<details>
  <summary>List of RR labels</summary>
  "Fact", "Issue", "ArgumentPetitioner", "ArgumentRespondent", "Statute", "Dissent", "PrecedentReliedUpon", "PrecedentNotReliedUpon", "PrecedentOverruled", "RulingByLowerCourt", "RatioOfTheDecision", "RulingByPresentCourt", "None"
</details>

---

---
### CJPE (Court Judgment Prediction and Explanation)

CJPE requires, given the facts and other details of a court case, predicting the final outcome, i.e., appeal accepted/rejected (Prediction), as well as identifying the salient sentences leading to the decision (Explanation).
In cases containing multiple appeals, the final outcome is accepted if at least one of the appeals are accepted, else rejected.

**Data Source:** The dataset consists of 34k Indian Supreme Court case documents. Out of these, 56 documents are annotated with the salient sentences by five legal experts.

**Data Splits:** The data is divided into 6 parts. 
For prediction, 'single_train' (5k docs) and 'single_dev' (2.5k docs) consist of cases having single appeals, while 'multi_train' (32k docs) and 'multi_dev' (1k docs) consist of cases having multiple appeals.
The 'test' split (1.5k) is the singular test set for both of these settings.
The 'expert' split (56 docs) contains documents annotated with the explanations (salient sentences).

**Data Instance:** An example from 'expert' looks as follows:
```json
{
  "id": "1951_10"
  "text": "CIVIL APPELLATE JURISDICTION Appeal (Civil Appeal No. 57 of 1950) from a judgment and decree of the High Court of Judicature at Bombay dated 1st April, 1948, in Appeal No. 365 of 1947 reversing a judgment of the Joint Civil Judge at Ahmedabad, dated 14th October, 1947 ..."
  "label": 1
  "expert_1": {
    "label": 1
    "rank1": ["Mr. Daphthary contended that the whole object ...", ...]
    "rank2": ["On a plain reading of the language of sections 12 and 50 ...", ...]
    "rank3": ["In our opinion, the decision of the appeal depends ...", ...]
    "rank4": ["It was contended before the High Court that ...", ...]
    "rank5": ["The appellants are owners of a property known as ...", ...]
  }
  "expert_2": {...}
  "expert_3": {...}
  "expert_4": {...}
  "expert_5": {...} 
}
```
Instances from all other splits have a similar structure, except that the "expert_*k*" keys have None values.

**Data Fields:**

* 'id': string &rarr; Case ID
* 'text': string &rarr; Full document text
* 'label': class_label &rarr; final decision
* 'expert_1':
    * 'label': class_label &rarr; final decision according to expert_1
    * 'rank1': List(string) &rarr; sentences leading to decision according to expert_1
    * 'rank2': List(string) &rarr; sentences contributing to decision according to expert_1
    * 'rank2': List(string) &rarr; sentences indicating the decision according to expert_1
    * 'rank2': List(string) &rarr; sentences without direct contribution but important for the case according to expert_1
    * 'rank2': List(string) &rarr; sentences without direct contribution but important for the case according to expert_1
* 'expert_2' &rarr; Similar to expert_1
* 'expert_3' &rarr; Similar to expert_1
* 'expert_4' &rarr; Similar to expert_1
* 'expert_5' &rarr; Similar to expert_1
  
<details>
  <summary>List of CJPE labels</summary>
  "REJECTED",  "ACCEPTED"
</details>

---

---
### BAIL (Bail Prediction)

BAIL aims to automatically predict whether the accused should be granted bail or not, given a criminal case document. 

**Data Source:** The dataset consists of a total of 176k docs (in Hindi) from different District Courts of Uttar Pradesh. 
All documents are segmented facts/arguments and judge opinion.

**Data Splits:** The data is divided into train, dev and test in two different ways. 
'train_all', 'dev_all' and 'test_all' are created by distributing the cases randomly.
'train_specific', 'dev_specific' and 'test_specific' are created by grouping docs from certain districts together.

**Data Instance:** An example from 'train_all' looks as follows:
```json
{
  "id": "Bail Application_2008_202101-04-2021407"
  "district": "agra"
  "text": {
    "facts-and-arguments": ["अग्रिम जमानत प्रार्थनापत्र के समर्थन में प्रार्थी, ...", "अभियोजन कथानक सक्षेंप में इस प्रकार ...", ...]
    "judge-opinion": ["प्रार्थी / अभियुक्तगण के विद्धान अधिवक्त ...", "पत्रावली के अवलोकन से स्पष्ट है कि अभियुक्तगण ...", ...]
  }
  "label": 0
}
```
Instances from all splits have a similar structure.

**Data Fields:**

* 'id': string &rarr; Case ID
* 'district': string &rarr; Name of the District Court
* 'text':
    * 'facts-and-arguments': List(string) &rarr; sentences containing facts and arguments by lawyers
    * 'judge-opinion': List(string) &rarr; sentences containing the opinion of the judge
* 'label': class_label &rarr; final bail decision
  
<details>
  <summary>List of BAIL labels</summary>
  "DENIED", "GRANTED"
</details>

---

---
### LSI (Legal Statute Identification)

LSI involves identifying the relevant statute(s) (written laws) given the facts of a court case document, from a predetermined set of target statutes.

**Data Source:** The dataset was created from 66k Indian Supreme Court and prominent High Court documents, each citing one or more statutes from a target set of 100 Indian Penal Code statutes.

**Data Splits:** The data is divided into 'train' (43k docs), 'dev' (10k docs) and 'test' (13k docs) splits. There is an additional 'statutes' split (100 docs) containing the description of the statutes.

**Data Instance:** An example from 'train' looks as follows:
```json
{
  "id": "100120460"
  "text": ["It is further alleged that present applicant ...", "Complainant also alleges in the FIR that ...", ...]
  "labels": [77, 71, 15, 74, 72, 16]
}
```
Instances from all 'dev' and 'test' have a similar structure. But, an example from 'statutes' looks as follows:
```json
{
  "id": "Section 120B"
  "text": ["Punishment of criminal conspiracy:", "(1) Whoever is a party to a criminal conspiracy ...", ...]
  "labels": None
}
```

**Data Fields:**

* 'id': string &rarr; IndianKanoon Case ID / IPC Section Number
* 'text': List(string) &rarr; sentences containing only the facts
* 'labels': List(class_label) &rarr; list of relevant statutes
  
<details>
  <summary>List of LSI labels</summary>
  <i>Section 2</i>, <i>Section 3</i>, <i>Section 4</i>, <i>Section 5</i>, <i>Section 13</i>, <i>Section 34</i>, <i>Section 107</i>, <i>Section 109</i>, <i>Section 114</i>, <i>Section 120</i>, <i>Section 120B</i>, <i>Section 143</i>, <i>Section 147</i>, <i>Section 148</i>, <i>Section 149</i>, <i>Section 155</i>, <i>Section 156</i>, <i>Section 161</i>, <i>Section 164</i>, <i>Section 173</i>, <i>Section 174A</i>, <i>Section 186</i>, <i>Section 188</i>, <i>Section 190</i>, <i>Section 193</i>, <i>Section 200</i>, <i>Section 201</i>, <i>Section 228</i>, <i>Section 229A</i>, <i>Section 279</i>, <i>Section 294</i>, <i>Section 294(b)</i>, <i>Section 299</i>, <i>Section 300</i>, <i>Section 302</i>, <i>Section 304</i>, <i>Section 304A</i>, <i>Section 304B</i>, <i>Section 306</i>, <i>Section 307</i>, <i>Section 308</i>, <i>Section 313</i>, <i>Section 320</i>, <i>Section 323</i>, <i>Section 324</i>, <i>Section 325</i>, <i>Section 326</i>, <i>Section 332</i>, <i>Section 336</i>, <i>Section 337</i>, <i>Section 338</i>, <i>Section 341</i>, <i>Section 342</i>, <i>Section 353</i>, <i>Section 354</i>, <i>Section 363</i>, <i>Section 364</i>, <i>Section 365</i>, <i>Section 366</i>, <i>Section 366A</i>, <i>Section 375</i>, <i>Section 376</i>, <i>Section 376(2)</i>, <i>Section 379</i>, <i>Section 380</i>, <i>Section 384</i>, <i>Section 389</i>, <i>Section 392</i>, <i>Section 394</i>, <i>Section 395</i>, <i>Section 397</i>, <i>Section 406</i>, <i>Section 409</i>, <i>Section 411</i>, <i>Section 415</i>, <i>Section 417</i>, <i>Section 419</i>, <i>Section 420</i>, <i>Section 427</i>, <i>Section 436</i>, <i>Section 437</i>, <i>Section 438</i>, <i>Section 447</i>, <i>Section 448</i>, <i>Section 450</i>, <i>Section 452</i>, <i>Section 457</i>, <i>Section 465</i>, <i>Section 467</i>, <i>Section 468</i>, <i>Section 471</i>, <i>Section 482</i>, <i>Section 494</i>, <i>Section 498</i>, <i>Section 498A</i>, <i>Section 500</i>, <i>Section 504</i>, <i>Section 506</i>, <i>Section 509</i>, <i>Section 511</i>
</details>

---

---
### PCR (Prior Case Retrieval)

PCR requires identifying relevant prior cases (based on facts and precedents) from a set of candidate case documents, given a query case document. 
The task is modeled as a pure retrieval task instead of multi-label classification since the candidate pool is large and dynamic.

**Data Source:** Both candidate and query documents (total 8k docs) are from the Indian Supreme Court.

**Data Splits:** Both queries and candidates are split for train/dev/test, resulting in 6 splits: 
'train_queries' (827 docs), 'dev_queries' (118 docs), 'test_queries' (237 docs), 
'train_candidates' (4.3k docs), 'dev_candidates' (1k docs), 'test_candidates' (1.7k docs).

**Data Instance:** An example from 'train_queries' looks as follows:
```json
{
  "id": "100120460"
  "text": ["CASE NO.: Appeal (civil) 2387 of 2001 ...", "THOMAS, J.", ...]
  "relevant_candidates": ["0000586994", "0000772259", "0001182839", "0001610057"]
}
```
Instances from 'dev_queries' and 'test_queries' have a similar structure. For '*_candidates' splits, the 'relevant_candidates' is None.


**Data Fields:**

* 'id': string &rarr; IndianKanoon Case ID
* 'text': List(string) &rarr; Full document text divided into sentences
* 'relevant_candidates': List(string) &rarr; list of relevant document IDs

---

---
### SUMM (Summarization)

SUMM automates the process of generating a gist (abstractive summary) of a legal case document that captures the critical aspects of the case. 
These summaries are similar to headnotes provided in many case documents.

**Data Source:** The dataset was created from 7.1k Indian Supreme Court case documents.

**Data Splits:** The data is divided into two splits: 'train' (7k docs) and 'test' (100 docs).

**Data Instance:** An example from 'train' looks as follows:
```json
{
  "id": "2858"
  "num_doc_tokens": 4867
  "num_summ_tokens": 708
  "document": ["Appeal No. 36 of 1967.", "Appeal by special leave from the judgment and order dated August 25, 1966 ...", ...]
  "summary": ["The appellant executed a usufructuary mortgage ...", "In 1949, the mortgagee left for Pakistan.", ...]
}
```
Instances from all splits have a similar structure.


**Data Fields:**

* 'id': string &rarr; IndianKanoon Case ID
* 'num_doc_tokens': int &rarr; the number of words in the full document
* 'num_summ_tokens': int &rarr; the number of words in the summary document
* 'document': List(string) &rarr; Full document text divided into sentences
* 'summary': List(string) &rarr; Summary text divided into sentences

---

---
### L-MT (Legal Machine Translation)

L-MT automates the process of converting a legal text in English to different Indic languages (Hindi, Bengali, etc.). 

**Data Source:** The dataset was created from Central Government Acts, Intellectual Property primers and FAQs by the Competition Commission of India.
There are a total of 6.6k en-xx pairs.

**Data Splits:** The data is divided into 'acts' (4k pairs), 'ip' (1k pairs), 'cci_faq' (1.4k pairs).

**Data Instance:** An example from 'acts' looks as follows:
```json
{
  "id": "2006_4_1_0/HI",
  "src_lang": "EN",
  "src": "1. Short title, extent and commencement.—",
  "tgt_lang": "HI",
  "tgt": "संक्षिप्त नाम, विस्तार और प्रारंभ--"
}
```
Instances from all splits have a similar structure.

**Data Fields:**

* 'id': string &rarr; Instance ID
* 'src_lang': string &rarr; Source language
* 'src': string &rarr; Source text
* 'tgt_lang': string &rarr; Target language
* 'tgt': string &rarr; Target text
  
---

## Benchmark Results

<table>
  <thead>
    <tr><th>Task</th><th>SOTA</th><th>Metric</th><th>Model</th></tr>
  </thead>
  <tbody>
    <tr><td>L-NER</td><td align="center">48.58%</td><td align="center">strict m-F1</td><td align="center">InLegalBERT + CRF</td></tr>
    <tr><td>RR</td><td align="center">69.01%</td><td align="center">m-F1</td><td align="center">MTL-BERT</td></tr>
    <tr><td rowspan=3>CJPE</td><td align="center">81.31%</td><td align="center">m-F1</td><td rowspan=3 align="center">InLegalBERT + BiLSTM</td></tr>
    <tr><td align="center">0.56</td><td align="center">ROUGE-L</td></tr>
    <tr><td align="center">0.32</td><td align="center">BLEU</td></tr>
    <tr><td>BAIL</td><td align="center">81%</td><td align="center">m-F1</td><td align="center">TF-IDF + IndicBERT</td></tr>
    <tr><td>LSI</td><td align="center">28.08%</td><td align="center">m-F1</td><td align="center">LeSICiN (Graph-based)</td></tr>
    <tr><td>PCR</td><td align="center">39.15%</td><td align="center">&#181;-F1@<i>K</i></td><td align="center">Event-based</td></tr>
    <tr><td rowspan=2>SUMM</td><td align="center">0.33</td><td align="center">ROUGE-L</td><td rowspan=2 align="center">Legal LED</td></tr>
    <tr><td align="center">0.86</td><td align="center">BERTScore</td></tr>
    <tr><td rowspan=3>L-MT</td><td align="center">0.28</td><td align="center">BLEU</td><td rowspan=3 align="center">MSFT (Microsoft Translation)</td></tr>
    <tr><td align="center">0.32</td><td align="center">GLEU</td></tr>
    <tr><td align="center">0.57</td><td align="center">chrF++</td></tr>
  </tbody>
</table>

## Citation Information
```
@inproceedings{iltur-2024,
      title = "IL-TUR: Benchmark for Indian Legal Text Understanding and Reasoning",
      author = "Joshi, Abhinav and Paul, Shounak and Sharma, Akshat and Goyal, Pawan and Ghosh, Saptarshi and Modi, Ashutosh"
      booktitle = "Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)",
      month = aug,
      year = "2024",
      address = "Bangkok, Thailand",
      publisher = "Association for Computational Linguistics",
  }
```

