from dataclasses import dataclass, asdict, fields
from datetime import datetime, timedelta
from typing import Any
import os
import pickle



@dataclass
class cache_data:
    """A class representing the contents of a file in the cache
    """
    cache_name:str
    cache_start_time:datetime
    cache_max_age:datetime
    cache_location:str
    cache_data:Any
    def as_dict(self) -> dict:
        """
        Returns:
            dict: A representation of the contents of a cache entry
        """
        return asdict(self)
    @classmethod
    def from_dict(cls, dict: dict[str,Any]) -> "cache_data":
        """Generates a new instance of `cache_data` from a given dictionary

        Args:
            dict (dict[str,Any]): The dictionary to be used

        Returns:
            cache_data: A new instance of `cache_data`
        """
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)
    def as_refrence(self) -> "cache_refrence":
        """Returns this entry as a reference to a file in the cache

        Returns:
            cache_refrence: The `cache_reference` for the file
        """
        return cache_refrence.from_cache_data(self)

@dataclass
class cache_refrence:
    """A class representing a pointer to an entry in the cache
    """
    cache_name:str
    cache_location:str
    cache_max_age:datetime
    @classmethod
    def from_dict(cls, dict: dict[str,Any]) -> "cache_refrence":
        """Generates a new `cache_reference` from a provided dictionary

        Args:
            dict (dict[str,Any]): The dictionary in questions

        Returns:
            cache_refrence: A new instance of `cache_reference`
        """
        sanitized = {}
        for field in fields(cls):
            val = dict.get(field.name)
            if val is not None:
                sanitized[field.name] = val
        return cls(**sanitized)
    @classmethod
    def from_cache_data(cls,data:cache_data)-> "cache_refrence":
        """Generates a new `cache_reference` from a `cache_data` instance representing the informnation to be referenced

        Args:
            data (cache_data): The `cache_data` instance to be referenced

        Returns:
            cache_refrence: A reference to the provided `cache_data` instance
        """
        return cls(data.cache_name,data.cache_location,data.cache_max_age)



class cache_manager:
    """
    Manages a physical data cache to reduce/limit database calls and increase performance
    """
    cache_location:str = "src/cache/"
    all_refrences:dict[str,cache_refrence] = {}

    def __init__(self):
        try:
            for f in os.listdir(self.cache_location):
                file = open(self.cache_location+f,"rb")
                data = cache_data.from_dict(pickle.Unpickler(file).load())
                ref = data.as_refrence()
                self.all_refrences[data.cache_name] = ref
        except FileNotFoundError as e:
            # no directory
            os.mkdir(self.cache_location)
        except EOFError as e:
            print("Cache bad, removing it")
            os.remove(self.cache_location+f) # type: ignore
            
        
    def add_to_cache(self,data:Any, name:str, timeout_seconds: float = 600.0) -> cache_refrence:
        now = datetime.now()
        timeout = now + timedelta(0,timeout_seconds)
        location = self.cache_location+name
        # check for exsisting file
        try:
            old_cache = self.get_cache(name)
            if old_cache.cache_max_age > now:
                # cache out still in date. 
                # NOT the update function, return old refrence
                return old_cache.as_refrence()
        except IOError:
            # cache dne safe to make new one
            pass
        except TypeError as e:
            print("Old cache formatted wrong, replacing")
        cache = cache_data(
            name,
            now,
            timeout,
            location,
            data
        )
        output = open(location, "wb")
        pickle.Pickler(output).dump(cache.as_dict())
        output.close()
        self.all_refrences[name] = cache.as_refrence()
        return cache.as_refrence()

    def get_cache(self,name: str) -> cache_data:
        location = self.cache_location+name
        if os.path.isfile(location):
            file = open(location, "rb")
            data = pickle.Unpickler(file).load()
            file.close()
            try:
                return cache_data.from_dict(data)
            except:
                raise TypeError(f"Cache {name} not formatted properly")
        raise IOError("Cache cache does not exsist")
    

    def update_cache(self,new_data:Any, refrence:cache_refrence, timeout_seconds: float = 600.0) -> cache_refrence:
        now = datetime.now()
        new_timeout = now + timedelta(0,timeout_seconds)
        # simply trust that the old cache is real... still
        old_cache = self.get_cache(refrence.cache_name)
        old_cache.cache_max_age = new_timeout
        old_cache.cache_data = new_data
        output = open(old_cache.cache_location, "wb")
        pickle.Pickler(output).dump(old_cache.as_dict())
        output.close()
        self.all_refrences[old_cache.cache_name] = old_cache.as_refrence()
        return old_cache.as_refrence()
    
    def remove_cache(self, refrence:cache_refrence) -> bool:
        if os.path.isfile(refrence.cache_location):
            # exsists
            os.remove(refrence.cache_location)
            del self.all_refrences[refrence.cache_name]
            return True
        return False