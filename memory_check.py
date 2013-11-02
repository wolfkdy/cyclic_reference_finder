# -*- coding: utf-8 -*-

import os
import gc
import time
import collections
import types

REPR_TOO_LARGE = 1024 * 10
REPR_NORMAL_SIZE = 512

# dfs
def dfs(son, parent, obj_graph, visited, dot_str_lst):
	id_son = id(son)
	id_parent = id(parent)
	if id_son in visited:
		for edge in obj_graph[id_parent]:
			if edge[1] == son:
				return True
	visited.add(id_son)
	for (edge_name, dst_node) in obj_graph[id_son]:
		if dfs(dst_node, son, obj_graph, visited, dot_str_lst):
			son_str = repr(son)
			if len(son_str) > REPR_NORMAL_SIZE:
				son_str = son_str[ : REPR_NORMAL_SIZE]
			dst_str = repr(dst_node)
			if len(dst_str) > REPR_NORMAL_SIZE:
				dst_str = dst_str[ : REPR_NORMAL_SIZE]
			dot_str_lst.append( '"%s" -> "%s" [ label = %s ];' % \
					(split(son_str.replace('"', "'")), split(dst_str.replace('"', "'")), edge_name,))
			return True
	visited.remove(id_son)
	return False

# objgraph [i] = [(j,k)...] # i -> src_node , j -> edge_name, k -> dst_node
def _CheckCycle(chk_list):
	obj_graph = {}
	obj_inv_table = {}
	obj_queue = collections.deque()
	visited = set()

	#make the state of obj_queue and visited consistency
	obj_queue.append(chk_list)
	visited.add(id(chk_list))

	chk_ids = [id(itm) for itm in chk_list] 
	def CheckAndPush(son):
		id_son = id(son)
		if id_son in visited:
			return
		visited.add(id_son)
		obj_queue.append(son)

	def type_ok(obj):
		if id(obj) not in chk_ids:
			return False
		if isinstance(obj, (tuple, list, dict, set)):
			return True
		# class-object or function-object
		if hasattr(obj, '__dict__'):
			return True
		#closure type
		if hasattr(obj, 'func_closure'):
			return True
		#closure upper_reference
		if hasattr(obj, 'cell_contents'):
			return True
		#bound method of an object, dynamic-set method of a class
		#how about im_func, im_class, any more?
		if hasattr(obj, 'im_self'):
			return True
		#local values of frame object
		if hasattr(obj, 'f_locals'):
			return True
		#global values of frmae object
		if hasattr(obj, 'f_globals'):
			return True
		return False

	# build objgraph
	while len(obj_queue) != 0:
		tmp = obj_queue.popleft()
		id_tmp = id(tmp)
		obj_inv_table[id_tmp] = tmp
		obj_graph[id_tmp] = []
		if isinstance(tmp, set):
			obj_graph[id_tmp].extend([('set_iter', v) for v in tmp if type_ok(v)])
			for pair in obj_graph[id_tmp]:
				CheckAndPush(pair[1])
		elif isinstance(tmp, dict):
			obj_graph[id_tmp].extend([(k, v) for k, v in tmp.iteritems() if type_ok(v)])
			for pair in obj_graph[id_tmp]:
				CheckAndPush(pair[1])
		elif isinstance(tmp, (tuple, list)):
			obj_graph[id_tmp].extend([(i, tmp[i]) for i in xrange(len(tmp)) if type_ok(tmp[i])])
			for pair in obj_graph[id_tmp]:
				CheckAndPush(pair[1])

		if hasattr(tmp, '__dict__'):
			obj_graph[id_tmp].extend([(k, v) for k, v in tmp.__dict__.iteritems() if type_ok(v)])
			for pair in obj_graph[id_tmp]:
				CheckAndPush(pair[1])

		if hasattr(tmp, 'func_closure'):
			f_c = tmp.func_closure
			if f_c is not None and type_ok(f_c):
				obj_graph[id_tmp].append(('func_closure', f_c))
				CheckAndPush(f_c)

		if hasattr(tmp, 'cell_contents'):
			cell_contents = tmp.cell_contents
			if type_ok(cell_contents):
				obj_graph[id_tmp].append(('cell_contents', cell_contents))
				CheckAndPush(cell_contents)

		if hasattr(tmp, 'im_self'):
			im_self = tmp.im_self
			if type_ok(im_self):
				obj_graph[id_tmp].append(('im_self', im_self))
				CheckAndPush(im_self)

		if hasattr(tmp, 'f_locals'):
			f_locals = tmp.f_locals
			if type_ok(f_locals):
				obj_graph[id_tmp].append(('f_locals', f_locals))
				CheckAndPush(f_locals)

		if hasattr(tmp ,'f_globals'):
			f_globals = tmp.f_globals
			if type_ok(f_globals):
				obj_graph[id_tmp].append(('f_globals', f_globals))
				CheckAndPush(f_globals)

	visited = set()
	dot_str_lst = []
	ret = dfs(chk_list, None, obj_graph, visited , dot_str_lst)
	if not ret:
		return ret
	dump_cycle_dot_str(dot_str_lst)
	return ret

def split(s):
	l = len(s)
	if l > 30:
		s = '%s\\n%s' % (split(s[: 30]), split(s[30 :]))
	return s

def dump_cycle_dot_str(str_lst):
	dot_str = """digraph "cycle_check"{
			rankdir=LR;
			size="200,200"
			node [shape = box];
			%s
		}
	""" % ('\n'.join([s for s in str_lst]), )
	prof_dir = os.path.join(os.getcwd(), "cycle")
	if not os.path.exists(prof_dir):
		os.makedirs(prof_dir)
	file_name = os.path.join(prof_dir,
			"cycle_%s.dot" % (time.strftime("%Y%m%d_%H%M"), ))
	fd = open(file_name, "w")
	fd.write(dot_str)

def gc_collect_cb(obj_lst):
	print('gc collect callback')
	for itm in obj_lst:
		s = repr(itm)
		if len(s) > REPR_NORMAL_SIZE:
			s = s[ : REPR_NORMAL_SIZE]
		print('Cycle Check Entitis', 'cycled obj', s)
	ret = _CheckCycle(obj_lst, CHK_CLOSURE)
	if not ret:
		#if gc callback occurs, and no cycle find, there must be somewhere we forget to add edges
		print('Cycle check no circle found')

def __Start__():
	if hasattr(gc, 'set_collect_callback'):
		gc.set_collect_callback(gc_collect_cb)

