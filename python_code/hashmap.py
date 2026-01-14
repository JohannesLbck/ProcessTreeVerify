import json
import os

class HashTable:

    # Create empty bucket list of given size
    def __init__(self, size):
        self.size = size
        self.hash_table = self.create_buckets()

    def create_buckets(self):
        return [[] for _ in range(self.size)]

    # save to disk
    def save_disk(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.hash_table, f)
    # load from disk
    def load_disk(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                self.hash_table = json.load(f)
        else:
            self.save_disk(filename)
    
    # check if a key exists in the hashmap
    def exists(self, key):
        hashed_key = hash(key) % self.size
        bucket = self.hash_table[hashed_key]
        for index, record in enumerate(bucket):
            record_key, record_val = record

            if record_key == key:
                return True
        return False

    # Insert values into hash map
    def insert(self, key, val):
        hashed_key = hash(key) % self.size
        bucket = self.hash_table[hashed_key]#
        found = False
        for index, record in enumerate(bucket):
            record_key, record_val = record
            if record_key == key:
                found = True
                break
        if found:
            bucket[index] = (key, val)
        else:
            bucket.append((key, val))

    # Return searched value with specific key
    def get(self, key):
        hashed_key = hash(key) % self.size
        bucket = self.hash_table[hashed_key]
        found = False
        for index, record in enumerate(bucket):
            record_key, record_val = record
            if record_key == key:
                found = True
                break
        if found:
            return record_val
        else:
            return "No record found"

    # Remove a value with specific key
    def delete(self, key):
      
        hashed_key = hash(key) % self.size
        bucket = self.hash_table[hashed_key]
        found_key = False
        for index, record in enumerate(bucket):
            record_key, record_val = record
            
            # check if the bucket has same key as
            # the key to be deleted
            if record_key == key:
                found_key = True
                break
        if found_key:
            bucket.pop(index)
        return

    # To print the items of hash map
    def __str__(self):
        return "".join(str(item) for item in self.hash_table)


constraints_t = HashTable(20)
constraints_t.load_disk("../../Voter/Constraints.json")

hash_t= HashTable(20)
hash_t.load_disk("TrackedUIDsHashmap.json")
