from .db import Db


class UserQnaToken:
    def __init__(self):
        self.db = Db().getDb()

    def save_qna_token(
        self,
        user_id,
        question,
        answer,
        prompt_tokens,
        chat_history_tokens,
        question_tokens,
        final_answer_tokens,
        total_tokens,
    ):
        usage_fee = total_tokens * 0.01  # 원
        try:
            with self.db.cursor() as cursor:
                sql = """
                INSERT INTO TokenUsageLog (
                    user_id, question, answer,
                    prompt_tokens, chat_history_tokens, question_tokens, final_answer_tokens, total_tokens, usage_fee
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                values = (
                    user_id,
                    question,
                    answer,
                    prompt_tokens,
                    chat_history_tokens,
                    question_tokens,
                    final_answer_tokens,
                    total_tokens,
                    usage_fee,
                )

                cursor.execute(sql, values)
            self.db.commit()
        except Exception as e:
            print("[token 저장 오류]", e)
            self.db.rollback()

    def get_total_usage_fee(self, user_id):
        try:
            with self.db.cursor() as cursor:
                sql = """
                SELECT IFNULL(SUM(usage_fee), 0) AS total_usage_fee
                FROM TokenUsageLog
                WHERE user_id = %s
                """
                cursor.execute(sql, (user_id,))
                result = cursor.fetchone()
                if result:
                    # DictCursor가 아니면 result[0]에서 꺼냄
                    return (
                        result["total_usage_fee"]
                        if isinstance(result, dict)
                        else result[0]
                    )
                else:
                    return 0.0
        except Exception as e:
            print("[token 총합 조회 오류]", e)
            return 0.0
