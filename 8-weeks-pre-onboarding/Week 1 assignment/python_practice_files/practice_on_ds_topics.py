# quick sort
def partition(arr, low, high):
    pivot = arr[high]
    i = low-1
    for j in range(low, high):
        if arr[j]<= pivot:
            i+=1
            arr[i],arr[j] = arr[j],arr[i]
    arr[i+1] , arr[high] = arr[high] , arr[i+1]
    return i+1

def quicksort(arr, low, high):
    if low < high:
        pi = partition(arr, low, high)
        quicksort(arr, low, pi-1)
        quicksort(arr, pi+1, high)

    return arr

# merge sort
def merge(arr, left, mid, right):
    n1 = mid - left+1
    n2 = right - mid
    l = [0]*n1
    r = [0]*n2
    for i in range(n1):
        l[i] = arr[left+i]
    for j in range(n2):
        r[j] = arr[mid+1+j]

    i = 0
    j = 0
    k = left
    while i<n1 and j<n2:
        if l[i]<=r[j]:
            arr[k] = l[i]
            i+=1
        else:
            arr[k] = r[j]
            j+=1
        k+=1
    while i<n1:
        arr[k] = l[i]
        i+=1
        k+=1

    while j<n2:
        arr[k] = r[j]
        j+=1
        k +=1

def mergesort(arr, left, right):
    if(left<right):
        mid = (left+right)//2
        mergesort(arr, left,mid)
        mergesort(arr, mid+1, right)
        merge(arr, left, mid, right)
    return arr

#insertion srot
def insertionSort(arr):
    n = len(arr)
    for i in range(1,n):
        key = arr[i]
        j = i-1
        while j>=0 and arr[j]<key:
            arr[j+1] = arr[j]
            j-=1
        arr[j+1] = key
    return arr

#selection sort 
def selection_sort(arr):
    n = len(arr)
    for i in range(n-1):
        min_index = i
        for j in range(i+1, n):
            if(arr[j]<arr[min_index]):
                min_index = j
        arr[i] , arr[min_index] = arr[min_index], arr[i]
    return arr

# arr=[2,1,3,0,5]

# print(selection_sort(arr))


# move all zeros to end

def move_zerostoend(arr):
    j = 0
    for i in range(len(arr)):
        if(arr[i] != 0):
            arr[i], arr[j] = arr[j], arr[i]
            j+=1
        
    return arr

#leader 
def leader(arr):
    lead = []
    max_e = arr[-1]
    lead.append(max_e)
    for i in range(len(arr)-2, -1, -1):
        if(arr[i]>=max_e):
            max_e = arr[i]
            lead.append(arr[i])
            
    return lead
        
def revword(s):
    s = list(s.split(" "))
    l = 0
    r = len(s)-1
    while l<r:
        s[l] , s[r] = s[r] , s[l]
        l+=1
        r-=1
    return " ".join(s)

def max_water(arr):
    left = 0
    right = len(arr)-1
    max_area = 0
    while left<right:
        width = right - left
        area = min(arr[left], arr[right])*width
        max_area = max(area, max_area)
        if(arr[left]<arr[right]):
            left+=1
        else:
            right -=1
    return max_area

#remove duplicates
def remove_dups(arr):
    set1 = set(arr)
    return list(set1)

#sum of triplets = 0
def threesum(nums):
    nums.sort()
    result = []
    n = len(nums)
    for i in range(n-2):
        if(i>0 and nums[i] == nums[i-1]):
            continue
        left = i+1
        right = n-1
        while left<right:
            total = nums[i] + nums[left] + nums [right]
            if total == 0:
                result.append([nums[i],nums[left],nums[right]])
                while left<right and nums[left]==nums[left+1]:
                    left += 1
                while left<right and nums[right]==nums[right-1]:
                    right -=1
                left += 1  
                right -= 1
            elif total<0:
                left+=1
            else:
                right -=1
    return result

#rain water
def trapped(height):
    left = 0
    right = len(height)-1
    leftmax = rightmax = water = 0
    while left<right:
        if height[left] < height[right]:
            if height[left]>= leftmax:
                leftmax = height[left]
            else:
                water += leftmax - height[left]
            left+=1
        else:
            if height[right]>=rightmax:
                rightmax = height[right]
            else:
                water += rightmax-height[right]
            right-=1
    return water


#sliding window max subarray
def maxsubarray(arr, k):
    window_sum = sum(arr[:k])
    max_sum = window_sum
    for i in range(k,len(arr)):
        window_sum = window_sum - arr[i-k] + arr[i]
        max_sum = max(window_sum, max_sum)
    return max_sum

# negative in window
def findfirstnegativeinwindow(arr, k):
    result = []
    for i in range(len(arr)-k+1):
        found = False
        for j in range(i, i+k):
            if(arr[j]<0):
                found = True
                result.append(arr[j])
                break
        if not found:
            result.append(0)
    return result

# sum of window to target
def longest_subarray_sum(arr, target):
    prefixsum = 0
    maxlen = 0
    prefix_map={0:-1}
    for i in range(len(arr)):
        prefixsum += arr[i]
        if (prefixsum==target):
            maxlen = i+1
        if(prefixsum-target) in prefix_map:
            length = i-prefix_map[prefixsum - target]
            maxlen = max(maxlen, length)
        if prefixsum not in prefix_map:
            prefix_map[prefixsum] = i
    return maxlen

#longest substrubg with distinct characters
def long_sub_array_distinct_chat(arr, k):
    left = 0
    max_len = 0
    count = {}
    for right in range(len(arr)):
        count[arr[right]] = count.get(arr[right],0)+1
        while len(count)>k:
            count[arr[left]] -= 1
            if(count[arr[left]])==0:
                del count[arr[left]]
            left +=1
        max_len = max(max_len, right-left+1)
    return max_len

#window with longest substring with no chars
def long_sub_str_unique(s):
    left = 0
    maxlen = 0
    charset = {}
    for right , char in enumerate(s):
        if char in charset and charset[char] >=left:
            left = charset[char]+1
        charset[char] = right
        maxlen = max(maxlen, right-left+1)
    return maxlen


#sum of targetr
def sum_of_target(arr, target):
    seen = {}
    for i, num in enumerate(arr):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

def appear_than_1(arr):
    freq = {}
    rep = []
    for i in range(len(arr)):
        freq[arr[i]] = freq.get(arr[i], 0)+1
    for i,j in freq.items():
        if j > 1:
            rep.append(i)
    return rep

def group_in(arr):
    freq = {}
    for i in arr:
       freq.setdefault(i,[]).append(i)
    return freq

def longest_consecutive(arr):
    s = set(arr)
    longest = 0
    for num in s:
        if num-1 not in s:
            length =1
            while num+length in s:
                length+=1
            longest = max(length, longest)
    return longest

def rev_words_in_sentense(txt):
    txt = list(txt.split(" "))
    print(txt)
    for i in range(len(txt)):
        txt[i] = txt[i][::-1]
    return " ".join(txt)


def max_sum_in_subarray(arr): #kdaynes algo
    max_sum = arr[0]
    current_sum = arr[0]
    start = end = temp = 0
    for i in range(1,len(arr)):
        if(arr[i]>current_sum+arr[i]):
            current_sum = arr[i]
            temp = i
        else:
            current_sum+=arr[i]
        if(current_sum>max_sum):
            max_sum = current_sum
            start = temp
            end = i
    return arr[start:end+1], max_sum

def max_product_of_subarray(arr):
    max_prod = arr[0]
    min_prod = arr[0]
    result = 0
    start = end = 0
    for i in range(1, len(arr)):
        if(arr[i]<0):
            max_prod, min_prod = min_prod, max_prod
        max_prod = max(arr[i], arr[i]*max_prod)
        min_prod = min(arr[i], min_prod*arr[i])

        result = max(max_prod, result)
    return result

def max_product_of_subarray_return_array(arr):# returns max_prod and its sub array     
    max_prod = min_prod = result = arr[0]
    max_start = min_start = res_start = res_end = 0
    for i in range(1, len(arr)):
        if(arr[i]<0):
            max_prod, min_prod = min_prod, max_prod
            max_start, min_start = min_start, max_start
        if(arr[i]>max_prod*arr[i]):
            max_prod = arr[i]
            max_start = i
        else:
            max_prod *= arr[i]
        if(arr[i]<min_prod*arr[i]):
            min_prod = arr[i]
            min_start = i
        else:
            min_prod *= arr[i]
        if(max_prod>result):
            result = max_prod
            res_start = max_start
            res_end = i
    return result, arr[res_start:res_end+1]

def zeros_to_end(arr):
    j = 0
    for i in range(len(arr)):
        if arr[i] != 0:
            arr[i], arr[j] = arr[j] , arr[i]
            j+=1
    return arr

def even_odd_seperation(arr):
    left = 0
    right = len(arr)-1
    while left<right:
        while left<right and arr[left]%2==0:
            left+=1
        while left<right and arr[right]%2==1:
            right-=1

        arr[left], arr[right] = arr[right], arr[left]
    return arr

def find_missing_1_to_n(arr):
    n = len(arr)+1
    total_sum = n * (n+1)//2
    arrsum = sum(arr)
    return total_sum - arrsum

def find_duplicate_using_floyids_cycle_detection(arr):
    try:
        slow = arr[0]
        fast = arr[0]
        while True:
            slow = arr[slow]
            fast = arr[arr[fast]]
            if slow == fast:
                break
        slow = arr[0]
        while slow!=fast:
            slow = arr[slow]
            fast = arr[fast]
        if slow:
            return slow
        return 0
    except IndexError:
        return 0
    
def floyids_triangle():
    num = 1
    for i in range(6):
        for j in range(i+1):
            print(num, end=" ")
            num+=1
        print()

def floyids_binary():
    for i in range(1,10):
        if i%2!=0:
            val = 1
        else:
            val = 0
        for j in range(1,i+1):
            print(val, end=" ")
            val = 1-val
        print()

def majority_element_booyer_more(arr):
    canditate = None
    count = 0
    for i in arr:
        if count == 0:
            canditate = i

        if i == canditate:
            count+=1
        else:
            count-=1
    # Second pass: Verify candidate
    count = 0
    for i in arr:
        if i == canditate:
            count += 1

    if count > len(arr) // 2:
        return canditate

    return -1

def product_except_self(arr):
    n = len(arr)
    prod = [1]*n
    prefix = 1
    sufix = 1
    for i in range(n):
        prod[i] = prefix
        prefix *= arr[i]
    for i in range(n-1,-1, -1):
        prod[i] *= sufix
        sufix *= arr[i]
    return prod

def merge_distinct_arrays_in_place(arr1, arr2):
    i = len(arr1)-1
    j = 0
    while i>=0 and j<len(arr2):
        if(arr1[i]>arr2[2]):
            arr1[i], arr2[j] = arr2[j], arr1[i]
            i-=1
            j+=1
        else:
            break
    arr1.sort()
    arr2.sort()
    return arr1, arr2


def next_gap(gap):
    if gap<=1:
        return 0
    return (gap+1)//2
def merge_distinct_arrays_optimal(arr1, arr2):
    n = len(arr1)
    m = len(arr2)
    gap = next_gap(n+m)
    while gap>0:
        i = 0
        j = gap
        while j<n + m:
            if i<n and j<n:
                if arr1[i]>arr1[j]:
                    arr1[i], arr1[j] = arr1[j], arr1[i]
            elif i<n and j>=n:
                if arr1[i] > arr2[j-n]:
                    arr1[i],arr2[j-n] = arr2[j-n], arr1[i]
            else:
                if arr2[i-n] > arr2[j-n]:
                    arr2[i-n], arr2[j-n] = arr2[j-n], arr2[i-n]
            i+=1
            j+=1
        gap = next_gap(gap)
    return arr1,arr2

def best_time_to_buyAndSell_stocks(arr):
    min_price = float('inf')
    max_profit = 0
    min_index = buy_index = sell_index = 0
    for i in arr:
        if i < min_price:
            min_price = i
            min_index = i
        profit = i-min_price
        if profit>max_profit:
            max_profit = profit
            buy_index = min_index
            sell_index = i
    return max_profit, f"{buy_index} : {sell_index}"

def rotate_array(arr, left, right):
    while(left<right):
        arr[left], arr[right] = arr[right], arr[left]
        left+=1
        right-=1
def array_right_rotation(arr, positon):
    n = len(arr)
    positon = positon % n
    rotate_array(arr, 0, n-1)
    rotate_array(arr, 0, positon-1)
    rotate_array(arr, positon, n-1)
    return arr
def array_left_rotation(arr, position):
    n = len(arr)
    position = position % n
    rotate_array(arr, 0, position-1)
    rotate_array(arr, position, n-1)
    rotate_array(arr, 0, n-1)
    return arr

def sort_012(arr): # dutch notation
    low = 0
    high = len(arr)-1
    mid = 0
    while mid<=high:
        if arr[mid]==0:
            arr[low], arr[mid] = arr[mid], arr[low]
            low+=1
            mid+=1
        elif arr[mid]==1:
            mid+=1
        else:
            arr[mid],arr[high] = arr[high], arr[mid]
            high -=1
    return arr


def tapping_rainwater(arr):
    left = 0
    right = len(arr)-1
    left_max = right_max = water_level = 0
    while left<right:
        if arr[left]<arr[right]:
            if arr[left]>= left_max:
                left_max = arr[left]
            else:
                water_level += left_max - arr[left]
            
            left += 1

        else:
            if arr[right]>=right_max:
                right_max = arr[right]
            else:
                water_level +=  right_max - arr[right]
            
            right -=1

    return water_level

#########   kadaynes max sub array
def kadyanes_max_subarray(arr):
    current = maximum = arr[0]
    for i in range(1, len(arr)):
        current = max(arr[i], current + arr[i])
        maximum = max(current, maximum)
    return maximum

def kadyanes_min_subarray(arr):
    current = minimum = arr[0]
    for i in range(1, len(arr)):
        current = min(arr[i], current + arr[i])
        minimum = min(current, minimum)
    return minimum

## kadyanes maximun circular subarray

def kadyanes_circular_max_subarray(arr):
    maximum = kadyanes_max_subarray(arr)
    if maximum<0:
        return maximum
    total = sum(arr)
    minimum = kadyanes_min_subarray(arr)
    circular = total-minimum
    return max(maximum, circular)

##### over lapping intervals

def overlapping_intervals(arr):
    if not arr:
        return []
    arr.sort(key = lambda x:x[0])
    merged = [arr[0]]
    for i in range(1,len(arr)):
        last = merged[-1]
        if arr[i][0]<=last[1]:
            last[1] = max(last[1], arr[i][1])
        else:
            merged.append(arr[i])
    return merged

# anagram
def anagram(s, s1):
    return sorted(s)==sorted(s1)


# longest substring without repeating chars
def long_substring_without_character_Repear(s):
    seen = set()
    left = 0
    max_len = 0
    for right in range(len(s)):
        while s[right] in seen:
            seen.remove(s[left])
            left+=1
        seen.add(s[right])
        max_len = max(max_len, right - left+1)
    return max_len, seen

# longest palindromic substring manacher's algorithm
def longest_substring_manachers(s):
    t = "^#" + "#".join(s) + "#$"
    l = len(t)
    p=[0]*l
    center = right = 0
    for i in range(1, l-1):
        mirror = 2*center - i
        if(i<right):
            p[i] = min(right-i, p[mirror])
        while t[i+p[i]+1] == t[i-p[i]-1]:
            p[i] +=1
        if i+p[i] >right:
            right = p[i]+i
            center = i
    max_len = max(p)
    center_index = p.index(max_len)
    start = (center_index-max_len)//2

    # to calculate total number of substrings
    ans = 0
    for i in p:
        ans += (i+1)//2
    #return ans   ##-->>> here is the count of howmany palindromic strings

    return s[start:start+max_len]

def longest_substring(s):
    start = end = 0
    def expand(left, right):
        while left>=0 and right < len(s) and s[left] == s[right]:
            left-=1
            right+=1
        return left+1,right-1
    for i in range(len(s)):
        l1 , r1 = expand(i,i)
        l2, r2 = expand(i,i+1)
        if(r1-l1 > end - start):
            start , end = l1, r1
        if(r2-l2>end-start):
            start , end = l2, r2
    return s[start:end+1]

def count_number_of_palindromes(s):
    def expand_arount(left, right):
        count = 0
        while left>=0 and right<len(s) and s[left]==s[right]:
            count +=1
            left -=1
            right +=1
        return count
    ans = 0
    for i in range(len(s)):
        ans+= expand_arount(i,i)
        ans+=expand_arount(i,i+1)
    return ans

def is_valid_paranthesis(s):
    stack = []
    pairs = {
        ")" : "(",
         "}":"{",
         "]":"["
    }
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        else:
            if not stack or stack.pop() !=pairs[ch]:
                return False
    return len(stack)==0

# grouped anagrams
def grouped_anagrams(s):
    groups = {}
    for word in s:
        key = "".join(sorted(word))
        if key not in groups:
            groups[key]=[]
        groups[key].append(word)
    return list(groups.values())

def compressor(s):
    read = write = 0
    while read<len(s):
        curent = s[read]
        count = 0
        while read<len(s) and s[read]==curent:
            read+=1
            count+=1
        s[write]=curent
        write+=1
        if count>1:
            for i in str(count):
                s[write] = i
                write+=1
    return write

# chars = ["a","a","b","b","c","c","c"]
# print(chars[:compressor(chars)] )

#reverse words in a string
def rev_words_in_string(txt):
    s = txt.split()
    # s.reverse()
    # s= " ".join(s)
    # return s
    left = 0
    right = len(s)-1
    while left<right:
        s[left],s[right] = s[right],s[left]
        left +=1
        right -=1
    return " ".join(s)

# nin window sub string
from collections import Counter

def min_window_substring(s,t):
    if not s or not t:
        return ""
    left = start = 0
    need = Counter(t)
    missing = len(t)
    min_val = float('inf')

    for right in range(len(s)):
        if need[s[right]]>0:
            missing -=1
        need[s[right]] -=1
        while missing==0:
            if right-left+1<min_val:
                min_val = right-left+1
                start = left
            need[s[left]]+=1
            if need[s[left]]>0:
                missing+=1
            left+=1
    if min_val == float('inf'):
        return ""
    return s[start:start+min_val]

#longest common prefix

def longest_common_prefix(s):
    if not s:
        return ""
    prefix = ""
    for i in range(len(s[0])):
        ch = s[0][i]
        for j in range(1,len(s)):
            if s[j][i] != ch or i>len(s[j]):
                return prefix
        prefix += ch
    return prefix

def isomorphic_string(s,t):
    if len(s) != len(t):
        return False
    s_to_t = {}
    t_to_s = {}
    for c1, c2 in zip(s,t):
        if c1 in s_to_t:
            if s_to_t[c1]!=c2:
                return False
        else:
            s_to_t[c1]=c2
        
        if c2 in t_to_s:
            if t_to_s[c2]!=c1:
                return False
        else:
            t_to_s[c2]=c1
    return True
#count owls and consonents
def count_owls_consonents(txt):
    txt =txt.lower()
    owl = consonent = 0
    for i in txt:
        if i in "aeiou":
            owl+=1
        if i in "bcdfghjklmnpqrstvwxyz":
            consonent+=1
    return owl, consonent

# remove spaces from str
def remove_spaces_from_string(s):
    s = "".join(s.split(" "))
    return s

def find_all_anagrams(s,t):
    if len(t)>len(s):
        return []
    need = Counter(t)
    ans = []
    left = 0
    window = Counter()
    for right in range(len(s)):
        window[s[right]]+=1
        if right-left+1 > len(t):
            window[s[left]]-=1

            if window[s[left]]==0:
                del window[s[left]]

            left+=1

        if window==need:
            ans.append(left)
    return ans

def is_string_rotated(s1, s2):
    if len(s1)!=len(s2):
        return False
    return s2 in (s1+s1)


# sliding window of str in str:
def str_in_str_sliding_window(s,t):

    for i in range(len(s)-len(t)+1):
        match = True
        for j in range(len(t)):
            if s[i+j] != t[j]:
                match = False
                break
        if match:
            return i
    return -1
#uidng knuth morris pattern
def build_lps(pattern):
    m = len(pattern)
    lps = [0]*m
    length = 0
    i = 1
    while i<m:
        if pattern[i] == pattern[length]:
            length+=1
            lps[i] = length
            i+=1
        elif length!=0:
            length = lps[length-1]
        else:
            lps[i] = 0
            i+=1
    return lps

def kmp_str_in_str(txt, pattern):
    if not txt or not pattern:
        return 0
    i = j = 0
    lps = build_lps(pattern)
    while i < len(txt):
        if txt[i] == pattern[j]:
            i+=1
            j+=1
            if j==len(pattern):
                return i-j
        elif j!=0:
            j = lps[j-1]
        else:
            i+=1
    return -1
# print(kmp_str_in_str("ababcabcabababd", "abc"))

def three_sum(arr):
    arr.sort()
    result = []
    n = len(arr)
    for i in range(n-2):
        if i>0 and arr[i]==arr[i-1]:
            continue
        left = i+1
        right = n-1
        while left<right:
            total = arr[i]+arr[left]+arr[right]
            if total<0:
                left+=1
            elif total>0:
                right-=1
            else:
                result.append([arr[i],arr[left],arr[right]])
                left+=1
                right-=1
                
                while left<right and arr[left]==arr[left-1]:
                    left+=1
                while left<right and arr[right]==arr[right+1]:
                    right-=1
    return result


# prefix sum 
def subarray_sum_count(arr, target):
    prefix_map = {0:1}
    prefix_sum = 0
    count = 0
    for i in arr:
        prefix_sum+=i
        if prefix_sum-target in prefix_map:
            count += prefix_map[prefix_sum-target]
        prefix_map[prefix_sum] = prefix_map.get(prefix_sum,0)+1
    return count


# print(subarray_sum_count([-1,-2,3,4,5,-2],3))


def count_consequtive_nums(arr):
    if not arr:
        return 0
    current = longest = 1
    for i in range(1,len(arr)):
        if (arr[i]==arr[i-1]):
            continue
        elif arr[i] == arr[i-1]+1:
            current+=1
        else:
            longest= max(longest,current)
            current = 1
    return max(longest, current)

def count_consecutive_nums_using_hash(arr):
    if not arr:
        return 0
    seen = set(arr)
    longest = 0
    for i in seen:
        if i-1 not in seen:
            current = i
            length = 1
            while current+1 in seen:
                current+=1
                length+=1
            longest = max(length, longest)
    return longest

def find_duplicates_in_arr(arr):
    seen = set()
    duplicate = set()
    for i in arr:
        if i in seen:
            duplicate.add(i)
        elif i not in seen:
            seen.add(i)
    return duplicate

def find_duplicate_in_arr_using_hashing(arr):
    freq = {}
    duplicates = []
    for i in arr:
        freq[i] = freq.get(i,0)+1
    for i,j in freq.items():
        if j>1:
            duplicates.append(i)
    return duplicates

def top_k_frequency(arr):
    freq = {}
    max_val = float('-inf')
    repeated = 0
    for i in arr:
        freq[i] = freq.get(i,0)+1
    for i,j in freq.items():
        if j>max_val:
            max_val=j
            repeated = i
    return repeated

def building_prefix_arr(arr):
    n = len(arr)
    prefix_sum = [0]*n
    prefix_sum[0] = arr[0]
    for i in range(1,len(arr)):
        prefix_sum[i] = arr[i]+prefix_sum[i-1]
    return prefix_sum

def range_query(arr, left, right):
    if left==0:
        return arr[right]
    prefix = building_prefix_arr(arr) ## build once and query many times take it outside
    return prefix[right]-prefix[left-1]

#brute force
def range_query_broot_force(arr,left,right):
    if left==0:
        return arr[right]
    if right>=len(arr):
        return None
    sum = 0
    for i in range(left, right+1):
        sum +=arr[i]

    return sum
    
def check_subarray_sum_for_k(arr, k):
    remainder_map = {0:-1}
    prefix_sum = 0
    for i,num in enumerate(arr):
        prefix_sum+=num
        remainder = prefix_sum%k
        if remainder in remainder_map:
            if i-remainder_map[remainder]>=2:
                return True
        else:
            remainder_map[remainder] = remainder_map.get(remainder,0)+1
    return False

def container_with_most_water(arr):
    left = 0
    right = len(arr)-1
    total_water = 0
    while left<right:
        width = right-left
        h = min(arr[left], arr[right])
        total_water = max(total_water, width*h)
        if arr[left]<arr[right]:
            left+=1
        else:
            right-=1
    return total_water

def max_sum_subarray_k_window(arr, k):
    total = 0
    for i in range(len(arr)-k+1):
        total = max(total, sum(arr[i:i+k]))
    return total

def max_sum_subarray_k_window_subarray(arr,k):
    n = len(arr)
    if k>n:
        return None
    window_sum = sum(arr[:k])
    max_sum = window_sum
    start = 0
    for i in range(k,n):
        window_sum += arr[i] 
        window_sum -= arr[i-k]
        if window_sum > max_sum:
            max_sum = window_sum
            start = i-k+1
    return arr[start:start+k]

def longest_sub_array_k_distinct_chars_return_subarray(s, k):
    freq = {}
    maxi = 0
    left = 0
    start = 0
    for right in range(len(s)):
        freq[s[right]] = freq.get(s[right],0)+1
        while len(freq)>k:
            freq[s[left]]-=1
            if freq[s[left]]==0:
                del freq[s[left]]
            left+=1
        if right-left+1>maxi:
            maxi = right-left+1
            start = left
    return maxi,s[start:start+maxi]

def min_subarray_size(arr, target):
    start = left = current_sum = 0
    min_len= float('inf')
    for right in range(len(arr)):
        current_sum += arr[right]
        while current_sum>=target:
            if right-left+1<min_len:
                min_len = right-left+1
                start = left
            current_sum -= arr[left]
            left+=1
    if min_len==float('inf'):
        return []
    return min_len,arr[start:start+min_len]

def remove_duplicates_in_place(arr):
    arr.sort()
    write = 1
    for read in range(1,len(arr)):
        if arr[read]!=arr[read-1]:
            arr[write]=arr[read]
            write+=1
    del arr[write:]
    return arr

def character_replacement_substring(s,k):
    freq = {}
    max_freq = best_len = best_start = left = 0
    for right in range(len(s)):
        freq[s[right]] = freq.get(s[right],0)+1
        max_freq = max(max_freq, freq[s[right]])
        while (right-left+1)-max_freq>k:
            freq[s[left]]-=1
            left+=1
        if right-left+1>best_len:
            best_len = right-left+1
            best_start = left
    return best_len, s[best_start:best_start+best_len]

def fruits_in_basket(arr):
    freq = {}
    left = best_len = best_start = 0
    for right in range(len(arr)):
        freq[arr[right]] = freq.get(arr[right], 0)+1
        while len(freq)>2:
            freq[arr[left]]-=1
            if freq[arr[left]]==0:
                del freq[arr[left]]
            left+=1
        if right-left+1 >best_len:
            best_len = right-left+1
            best_start = left
    return best_len, arr[best_start:best_start+best_len]



print(fruits_in_basket([1,2,3,2,2]))