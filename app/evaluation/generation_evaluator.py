from generation_metrics import answer_token_recall


class GenerationEvaluator:

    def __init__(
        self,
        generator,
        evaluation_file,
        judge,
    ):
        self.generator = generator
        self.evaluation_file = evaluation_file
        self.judge = judge

    def load_dataset(self):
        import json

        with open(
            self.evaluation_file,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def evaluate(
        self,
        retrieval_pipeline,
        context_processor,
    ):
        dataset = self.load_dataset()

        results = []

        for item in dataset:

            question = item["question"]
            expected_answer = item["expected_answer"]

            # ------------------------------------------
            # Retrieval
            # ------------------------------------------

            retrieved = retrieval_pipeline.retrieve(
                question,
                top_k=5,
            )

            # ------------------------------------------
            # Context processing
            # ------------------------------------------

            contexts = context_processor.process(
                retrieved
            )

            # ------------------------------------------
            # Generation
            # ------------------------------------------

            generation = self.generator.generate(
                question,
                contexts,
            )

            generated_answer = generation["answer"]

            # ------------------------------------------
            # Token overlap
            # ------------------------------------------

            token_recall = answer_token_recall(
                generated_answer,
                expected_answer,
            )

            # ------------------------------------------
            # LLM Judge
            # ------------------------------------------

            judge_result = self.judge.evaluate(
                question=question,
                expected_answer=expected_answer,
                generated_answer=generated_answer,
                contexts=contexts,
            )

            # ------------------------------------------
            # Store result
            # ------------------------------------------

            results.append(
                {
                    "id": item["id"],
                    "question": question,
                    "expected_answer": expected_answer,
                    "generated_answer": generated_answer,
                    "token_recall": token_recall,

                    "correctness": judge_result[
                        "correctness"
                    ],

                    "relevance": judge_result[
                        "relevance"
                    ],

                    "faithfulness": judge_result[
                        "faithfulness"
                    ],

                    "judge_reason": judge_result[
                        "reason"
                    ],

                    "sources": generation["sources"],
                }
            )

        return results

    def summarize(self, results):

        if not results:
            return {}

        count = len(results)

        return {
            "queries": count,

            "average_token_recall": (
                sum(
                    result["token_recall"]
                    for result in results
                )
                / count
            ),

            "average_correctness": (
                sum(
                    result["correctness"]
                    for result in results
                )
                / count
            ),

            "average_relevance": (
                sum(
                    result["relevance"]
                    for result in results
                )
                / count
            ),

            "average_faithfulness": (
                sum(
                    result["faithfulness"]
                    for result in results
                )
                / count
            ),
        }