# Complexity Sketch

⇒ n_r = requirements, n_t = tree nodes, n_l = number of loop elements, n_te = number of terminates, n_c = number of calls (<n_t), number of resources n_re, n_d  

For req in requirements:  
	verify() ⇒  O(n_r)

## Exists

```
For call in n_t: ⇒ n_t  
	Compare label => 1  
	Return => 1
⇒ O(n_t)
```

## Absence
```
Not exists ⇒ O(n_t)
```
## Loop
```
Loops = tree.findall (“loops”) ⇒ O(n_t)  
For loop in loops: => O(n_l)  
	Exists ⇒ O(n_t)  
	Compare ⇒ 1  
⇒ O(n_t + n_l*(n_t) ⇒ Assume all are some high number n ⇒ O(n^2)
```
## Get_ancestors
```
For each in n_t: ⇒ O(n_t)  
	Compare ⇒ 1  
⇒ O(n_t)
```
## Get_shared_ancestors
```
get_ancestors() ⇒ O(n_t)  
For each ancestors ⇒ O(n_t)  
	Compare ⇒ 1  
⇒ O(n_t + n_t) ⇒ O(n_t)
```
## Compare_ele
```
get_shared_ancestors() ⇒ O(n_t)  
For ancestor in shared_ancestors() ⇒ O(n_t) Assuming that all other elements are shared ancestors  
	Compare ⇒ 1  

If: worst case:  
For ele in n_t: ⇒ O(n_t)  
	Compare ⇒ 1  

⇒ O(n_t + n_t) ⇒ O(n_t)
```
## Directly follows must
```
get_shared_ancestors() ⇒ O(n_t)  
For ancestor in shared_ancestors() ⇒ O(n_t)  
	Compares ⇒ 1  
Compares ⇒ 1  
For n in calls ⇒ O(n_t)  
	Compare ⇒ 1  

⇒ O(n_t + n_t + n_t) ⇒ O(n_t)
```
## Directly_follows
```
Exists ⇒ O(n_t)  
Exists ⇒ O(n_t)  

If a = terminate:  
	Return ⇒ 1  

ElseIf b = terminate:  
	For each n_te: O(n_te)  
		Directly follows must() ⇒ O(n_t)  
		Compare ⇒ 1  

Else:  
	Directly follows must() ⇒ O(n_t)  
	Compare ⇒ 1  

⇒ Worst case: O(n_t + n_t + n_te * n_t) where n_te < n_t ⇒ O(n^2)  

⇒ Note that this worst case is extremely unlikely as it requires that every single call in the process except for a is a terminate, in practice it is almost always O(n) and that previously all ancestors were shared ancestors, which even seems impossible, so likely we can show that it is O(n)
```
## Leads_to
```
Exists ⇒ O(n_t)  
Exists ⇒ O(n_t)  

If a:  
	If b:  
		compare_ele() ⇒ O(n_t)  
		Compares ⇒ 1  

⇒ O(n_t + n_t + n_t) ⇒ O(n_t)
```
## Precedence
```
Same as leads to with different compares  
⇒ O(n_t)
```
## Leads_to_absence
```
Same as leads to with different compares  
⇒ O(n_t)
```
## Precedence_absence
```
Same as leads to with different compares  
⇒ O(n_t)
```
## Parallel
```
Same as leads to with different compares  
⇒ O(n_t)
```
## Executed_by_identify
```
For each in n_t: ⇒ O(n_t)  
	Compares ⇒ 1  
	For each resource n_re: ⇒ O(n_re)  
		Compares ⇒ 1  

O(n_t * n_re) ⇒ assuming there are less resources than nodes in the process tree ⇒ O(n_t^2)  

⇒ Assuming the amount of resources is small enough to not be considered ⇒ O(n)
```
## executed_by_annotated
```
Call.find ⇒ searching in tree has complexity O(n), we search the subtree of the activity, so in practice much smaller than n_t ⇒ O(n_t)  
Compares ⇒ 1  

⇒ O(n_t)
```
## Executed_by
```
exists() ⇒ O(n_t)  

If worst case:  
	Executed_by annotated() ⇒ O(n_t)  
	For resource in resources: ⇒ O(n_re)  
		Compares ⇒ 1  

⇒ O(n_t + n_t + n_re) ⇒ Assuming there are less resources than nodes ⇒ O(n_t)
```
## Executed_by_return
```
exists() ⇒ O(n_t)  

If worst case:  
	For r in resources: ⇒ O(n_re)  
		Compares ⇒ 1  

⇒ O(n_t) ← Same as above
```
## timeouts_exists
```
For each in n_t: ⇒ O(n_t)  
	compares ⇒ 1  

⇒ O(n_t)
```
## Timed_alternative
```
exists() ⇒ O(n_t)  

If worst case:  
	exists() ⇒ O(n_t)  

	If worst case:  
		timeouts_exists() ⇒ O(n_t)  
		For each timeout: Assuming every node is a timeout ⇒ O(n_t)  
			Compares ⇒ 1  

⇒ O(n_t + n_t + n_t) ⇒ O(n_t)
```
## Sync_exists
```
For each in n_t: ⇒ O(n_t)  
	Compares ⇒ 1  

⇒ O(n_t)
```
## Min_time_between
```
Leads_to() ⇒ O(n_t)  
	exists() ⇒ O(n_t)  
	exists() ⇒ O(n_t)  
	Sync exists() ⇒ O(n_t)  

	For each sync ⇒ O(n_t) assuming that every node is a sync  

	If worst case:  
		Directly follows must() ⇒ O(n_t)  
		Directly follows must() ⇒ O(n_t)  
		Directly follows must() ⇒ O(n_t)  
		Compares ⇒ 1  

⇒ O(n_t^2) ⇒ Normally just O(n_t)
```
## by_due_date_annotated
```
For call in n_t: ⇒ O(n_t)  
	Compares ⇒ 1  

⇒ O(n_t)
```
## due_date_exists
```
For call in n_t: ⇒ O(n_t)  
	Compares ⇒ 1  

⇒ O(n_t)
```
## Condition_finder
```
For each in n_t: ⇒ O(n_t)  
	Compares ⇒ 1  

⇒ O(n_t)
```
## Condition_eventually_follows
```
condition_finder() ⇒ O(n_t)  

If worst case:  
	exists() ⇒ O(n_t)  

	If worst case:  
		compare_ele() ⇒ O(n_t)  

⇒ O(3 * n_t) ⇒ O(n_t)
```
## By_due_date_explicit
```
Exists() ⇒ O(n_t)  

If worst case:  
	Due date exists()  

For each due date ⇒ Worst case every node is a due date ⇒ O(n_t)  

return: condition eventually follows (so not multiplied) ⇒ O(n_t)  

⇒ O(n_t)
```
## By_due_date
```
Checks both above so  

⇒ O(n_t + n_t) ⇒ O(n_t)
```
## Max_time_between
```
exists() ⇒ O(n_t)  
exists() ⇒ O(n_t)  

If worst case:  
	If worst case:  
		timeout_exists() ⇒ O(n_t)  
			For each timeout ⇒ Assume all are timeouts ⇒ O(n_t)  
				compares ⇒ 1  

⇒ O(n_t)
```
## Data_objects
```
For call in n_t: ⇒ O(n_t)  
	Compares ⇒ 1  

⇒ O(n_t)
```
## Send_exists
```
data_objects() ⇒ O(n_t)  

For each in n_d ⇒ Can not assume that n_d is strictly smaller than n_t so ⇒ O(n_d)  
	Compares ⇒ 1  

⇒ O(n_t + n_d)
```
## Receive_exists
```
Data_objects() ⇒ O(n_t)  

For call in n_d ⇒ As above ⇒ O(n_d)  
	Compares ⇒ 1  

⇒ O(n_t + n_d)
```
## Activity_sends
```
exists() ⇒ O(n_t)  
Compares ⇒ 1  

⇒ O(n_t)
```
## Activity_receives
```
As above but with different compares  

⇒ O(n_t)
```
## Condition_directly_follows
```
condition_finder() ⇒ O(n_t)  
exists() ⇒ O(n_t)  

For ele in branch ⇒ branch is strictly less than tree so ⇒ O(n_t)  
	Compares ⇒ 1  

⇒ O(3 * n_t) ⇒ O(n_t)
```
## Condition_eventually_follows (Data)
```
condition_finder() ⇒ O(n_t)  

If worst case:  
	exists() ⇒ O(n_t)  

	If worst case:  
		compare_ele() ⇒ O(n_t)  
		Compares ⇒ 1  

⇒ O(n_t)
```
## Data leads to absence
```
Not condition eventually follows() ⇒ O(n_t)
```