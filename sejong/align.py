#!/usr/bin/env python
#-*- coding: utf8 -*-

import os
import copy
from optparse import OptionParser

# global variable
VERBOSE = 0

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def get_mlist(analyzed) :
	if not analyzed : return []
	try : 
		analyzed = analyzed.replace(' + ',' ')
		mlist = analyzed.split(' ')
	except : return []
	num = len(mlist)
	t_mlist = []
	for morph_tag in mlist :
		try :
			morph_tag = morph_tag.strip()
			pos = morph_tag.rfind('/')
			if pos == -1 : return []
			morph = morph_tag[0:pos]
			tag   = morph_tag[pos+1:]
		except : return []
		t_mlist += [(morph,tag)]
	return t_mlist

def split_row(n_bucket, seq, eoj, mlist, ptst, gov) :
	idx = 1
	mlist_max = len(mlist)
	for morph, tag in mlist :
		nseq = seq + '-' + str(idx)
		if idx != mlist_max : 
			ngov = seq + '-' + str(idx+1)
			nptst = 'MOD'
		else : 
			ngov = gov + '-' + '1'
			nptst = ptst
		if VERBOSE : print nseq + '\t' + morph + '\t' + tag + '\t' + nptst + '\t' + ngov
		n_bucket.append([nseq, morph, tag, nptst, ngov])
		idx += 1

def spill(bucket, extend) :
	n_bucket = []
	for line in bucket :
		seq,eoj,analyzed,ptst,gov = line.split('\t',4)
		mlist = get_mlist(analyzed)
		# 형태소 단위로 분리
		split_row(n_bucket, seq, eoj, mlist, ptst, gov)

	# re-numbering
	idx = 1
	map = {}
	for seq,morph,tag,ptst,gov in n_bucket :
		# seq에는 'seq-1' 등이 포함되어 있음
		map[seq] = idx
		idx += 1
	nn_bucket = []
	idx = 0
	max = len(n_bucket)
	for seq,morph,tag,ptst,gov in n_bucket :
		n_seq = map[seq]
		gov_srch = gov
		if gov_srch in map : n_gov = map[gov_srch]
		else : n_gov = 0
		nn_bucket.append([n_seq,morph,tag,ptst,n_gov])
		idx += 1

	# make extended corpus
	# 구두점이 있는 경우와 없는 경우 분석 결과가 달라지는 문제를 커버
	# ex) '이루 고 있 다 .' -> '이루 고 있 다'
	buckets = [nn_bucket]
	# 마지막 구두점 'SF'에 한정
	if extend and len(nn_bucket) >= 2 and nn_bucket[-1][2] == 'SF' :
		# 기존 마지막 형태소를 지배소로 갖는 의존소의 개수 확인
		last_seq = nn_bucket[-1][0]
		dependents_of_root = 0
		for seq,morph,tag,ptst,gov in nn_bucket :
			if gov == last_seq : dependents_of_root += 1
		# head-final 원칙에 의해서 1개일 경우만 확장한다.
		if dependents_of_root == 1 : 
			t_bucket = copy.deepcopy(nn_bucket[:-1])
			t_bucket[-1][3] = nn_bucket[-1][3] # 기존 마지막 형태소의 ptst 
			t_bucket[-1][4] = 0                # 마지막 형태소가 ROOT이므로 gov 0으로 설정
			buckets.append(t_bucket)

	# print CONLL-U format
	for bucket in buckets :
		for seq,morph,tag,ptst,gov in bucket :
			id = seq
			form = morph
			lemma = morph
			upostag = tag
			xpostag = tag
			feats = '_'
			head = gov
			deprel = ptst
			if gov == 0 : deprel = 'ROOT'
			deps = '_'
			misc = '_'
			print '\t'.join([str(e) for e in [id,form,lemma,upostag,xpostag,feats,head,deprel,deps,misc]])
		print '\n',

	return 1

if __name__ == '__main__':

	parser = OptionParser()
	parser.add_option("--verbose", action="store_const", const=1, dest="verbose", help="verbose mode")
	parser.add_option("-e", "--extend", dest="extend", type="int", default=0, help="set 1 for generating extended corpus", metavar="extend")
	(options, args) = parser.parse_args()

	if options.verbose : VERBOSE = 1
	extend = options.extend
	if not extend : extend = 0
	else : extend = 1

	number_of_sent = 0
	number_of_sent_skip = 0
	bucket = []
	while 1:
		try:
			line = sys.stdin.readline()
		except KeyboardInterrupt:
			break
		if not line:
			break
		line = line.strip()

		if not line and len(bucket) >= 1 : 
			ret = spill(bucket, options.extend)
			bucket = []
			number_of_sent += 1
			if ret == -1 : number_of_sent_skip += 1
			continue

		if line : bucket.append(line)

	if len(bucket) != 0 :
		ret = spill(bucket, options.extend)
		number_of_sent += 1
		if not ret : number_of_sent_skip += 1

	sys.stderr.write("number_of_sent = %d, number_of_sent_skip = %d\n" % (number_of_sent,number_of_sent_skip))
