# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## �����Ȃ�

Instagram �÷忰����� - Instagramn�÷忰�1�����W���ƣ��k;(Y����

## �z��

1. **Yyfnh:o�,�**: GUI����û����������oYyf�,�g�
2. **GitK(**: �����Bk�,�g�����û���\W���÷�
3. **�zէ��**: �z�.mdk�D���k�Œ2��

## �����L����

```bash
# ��n\h	�
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# �X��n�����
pip install -r requirements.txt

# GUIHn�L
python src/ui/tag_input_gui.py

# ����n�L
python src/run_batch.py

# �����cookie�X	
python src/scraper/login.py
```

## ���Ư�め

### �����

- **src/ui/tag_input_gui.py**: tkinter GUIn�����ݤ��^��ˢQn����j���է��
- **src/scraper/login.py**: InstagramK�����hcookie�X��C��
- **src/scraper/fetch_tag.py**: ����ï���1n֗h�����
- **src/scraper/utils.py**: Selenium�\nq�p�쯿���-�
- **src/run_batch.py**: CSVe�k��p��n ��
- **src/scheduler.py**: ��Ln�������

### ������

1. **�<���**: �oK����� � cookies/ig_cookies.json k�X � �Mo�թC
2. **��������**: GUI/��� � fetch_tag.py � Selenium�\ � ����� � CSV/JSON�X
3. **��������**: cookie1�� � �����B � �÷��C

### ́j-$�

- **Selenium(**: Instagram APIn6Pk���馶���\g���֗
- **cookie�**: ��n����Q�÷��8�g��
- **�쯿n�**: DOM	�k��W�YOY�_�utils.pyk�
- **�����_**: human_sleep()g���WD�\�!#W��

## �zBn��

1. **����ƣ**: .envա��ov�k����WjD�<�1o���k�KjD
2. **���6P**: N�j�����Q��Zhuman_sleep()�(
3. **����**: DOM	�cookie1����������k���
4. **����X**: data/hashtags/YYYYMM/ n%թ��� ��

## �(n�zէ��

�z�.mdk�eM�n�g��

1. ,1է��: ������-�ǣ���� 	
2. ,2է��: ��_����������	
3. ,3է��: UI�K(_�
4. ,4է��: ���<

է��n���s0o�z�.md��g