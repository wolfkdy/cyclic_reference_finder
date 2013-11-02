cyclic_reference_finder
=======================

gcmodule.c is from python2.7.2 source code.
I add MACRO #KDY_DEBUG to switch on gc collect callback.
If this macro is on, when gc does collect, the unreachable objects will pass to the script
layer and a full-pass bfs is done to find a reference cycle. 
If a cycle is found, a dot file will be gen to describe the cycle.

There is another way to do this job. You may set gc.set_debug(DEBUG_SAVEALL). then gc will not destroy the
unreachable objects. so you may start a timer and timely calls gc_collect_callback function.

Both methods work well
