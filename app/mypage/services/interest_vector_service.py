from app.mypage.services.keyword_service import KeywordService


class InterestVectorService:
    def __init__(self, dao):
        self.dao = dao

    def save_vector_with_keywords(self, user_id, user_vector):
        top_keywords = KeywordService.build_top_keywords(user_vector)
        print("DEBUG top_keywords:", top_keywords)
        self.dao.save_vector(user_id, user_vector, top_keywords)
        

    def load_vector(self, user_id):
        return self.dao.load_vector(user_id)
