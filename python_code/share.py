class Config:
    instance_id = None

    @classmethod
    def set_id(cls, Id):
        cls.instance_id = Id
    
    @classmethod
    def get_id(cls):
        return cls.instance_id



config = Config
