"""LeetCode and Rap catalogs: problem splitting, page rules and escaped rendering."""

from pathlib import Path
import tempfile
import unittest

from bs4 import BeautifulSoup

from site_content.catalog import RAP_PAGES, leetcode_catalog, rap_catalog
from site_content.catalog_views import LEETCODE_RULES, leetcode_content, rap_content

LEET = {
    "arrays_and_strings.py": '''"""

Arrays and Strings

"""

\'\'\'

# Max Consecutive Ones

nums = [1,1,0]
# nums = [0]

def findMaxConsecutiveOnes(nums):
    return 2

\'\'\'

# Fib (memo)

def fib(n, memo={}):
    if n < 2:
        return n
    memo[n] = fib(n - 1) + fib(n - 2)
    return memo[n]

# Next Problem



# Next Problem
''',
    "trees_and_tries.py": '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

###############################################
############### Trees and Tries ###############
###############################################

##########################################
###### Binary Trees Recursive Traversal ######
##########################################

# Pre-Order Traversal

def preorder(root):
    return [root.val] + preorder(root.left) if root else []

# Kth Largest Element in a Stream (11/12 cases passed, fails due to imbalanced BST)

class KthLargest:
    def add(self, val):
        return "<script>alert(1)</script>"

# Contains Duplicate III



# Construct Binary Tree from Inorder and Postorder Traversal

def buildTree(post, ino):
    return None
''',
    "biggest_prime.py": '''"""
Header
"""

import math

def is_prime(n):
    return n > 1

# print(is_prime(5))
# print(is_prime(6))
''',
}


class LeetCodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        repo = Path(cls.folder.name)
        for name, text in LEET.items():
            (repo / name).write_text(text, encoding="utf-8")
        cls.catalog = leetcode_catalog(repo)
        cls.by_title = {p["title"]: p for p in cls.catalog["problems"]}

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_problems_split_at_headings_only(self):
        self.assertEqual(set(self.by_title), {
            "Max Consecutive Ones", "Fib (memo)", "Pre-Order Traversal",
            "Kth Largest Element in a Stream (11/12 cases passed, fails due to imbalanced BST)",
            "Contains Duplicate III", "Construct Binary Tree from Inorder and Postorder Traversal", "Biggest Prime"})
        first = self.by_title["Max Consecutive Ones"]
        self.assertIn("# nums = [0]", first["code"], "commented test lines stay in the code")
        self.assertFalse(first["code"].endswith("'''"), "the closing string quote is trimmed")
        self.assertEqual(first["line"], 11)
        self.assertEqual(self.by_title["Pre-Order Traversal"]["group"], "Binary Trees Recursive Traversal")
        self.assertIn("is_prime", self.by_title["Biggest Prime"]["code"])
        self.assertIsNone(first["url"], "no Git remote, no link")

    def test_page_rules(self):
        pages = {title: problem["pages"] for title, problem in self.by_title.items()}
        self.assertEqual(pages["Max Consecutive Ones"], ["Lists-and-Arrays"])
        self.assertEqual(pages["Fib (memo)"], ["Lists-and-Arrays", "Dynamic-Programming", "Recursion"])
        self.assertEqual(pages["Pre-Order Traversal"], ["Trees-and-Tries", "Graphs", "Recursion"])
        self.assertEqual(pages["Construct Binary Tree from Inorder and Postorder Traversal"], ["Trees-and-Tries"])
        kth = self.by_title["Kth Largest Element in a Stream (11/12 cases passed, fails due to imbalanced BST)"]
        self.assertEqual((kth["status"], kth["pages"]), ("partial", ["Trees-and-Tries", "Hard-Problems"]))
        empty = self.by_title["Contains Duplicate III"]
        self.assertEqual((empty["status"], empty["pages"]), ("heading", ["Hard-Problems"]))
        self.assertEqual(set(LEETCODE_RULES), {"Lists-and-Arrays", "Trees-and-Tries", "Graphs", "Dynamic-Programming", "Recursion", "Hard-Problems"})

    def test_rendering_escapes_code_and_keeps_ids_unique(self):
        for page in LEETCODE_RULES:
            with self.subTest(page=page):
                lede, markup = leetcode_content(page, self.catalog, "../../../")
                soup = BeautifulSoup(markup, "html.parser")
                self.assertIsNone(soup.find("script"))
                ids = [tag["id"] for tag in soup.find_all(id=True)]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual([a["href"][1:] for a in soup.select(".catalog-index a")], [i for i in ids if i != "catalog-title"])
                self.assertTrue(lede)
        _, hard = leetcode_content("Hard-Problems", self.catalog, "../../../")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", hard)
        self.assertIn("Heading only", hard)
        lede, empty = leetcode_content("Dynamic-Programming", {**self.catalog, "problems": []}, "../../../")
        self.assertIn("No solutions", lede)
        self.assertIn("Science-and-Engineering/Computer-Science/Data-Structures-and-Algorithms/index.html", empty)


class RapTests(unittest.TestCase):
    def test_folders_map_to_pages_and_tools_show_on_future_projects(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            for path, text in {"Vagabond/HALT.txt": "Line one\n\n<b>Line two</b>\n", "Vagabond/._HALT.txt": "metadata",
                               "New_Folder/Idea.txt": "draft", "notes.txt": "root", "music_visualizer.py": "print('viz')\n",
                               "Seven_Deadly_Sins2_v1/Envy_V1.txt": "envy"}.items():
                (repo / path).parent.mkdir(parents=True, exist_ok=True)
                (repo / path).write_text(text, encoding="utf-8")
            catalog = rap_catalog(repo)
        songs = {song["path"]: song for song in catalog["songs"]}
        self.assertEqual(set(songs), {"Vagabond/HALT.txt", "New_Folder/Idea.txt", "Seven_Deadly_Sins2_v1/Envy_V1.txt"})
        self.assertEqual(songs["Vagabond/HALT.txt"]["page"], "Vagabond")
        self.assertEqual(songs["Vagabond/HALT.txt"]["lines"], 2)
        self.assertEqual(songs["New_Folder/Idea.txt"]["page"], "Future-Projects", "unplaced folders are never dropped")
        self.assertEqual(songs["Seven_Deadly_Sins2_v1/Envy_V1.txt"]["folderTitle"], "Seven Deadly Sins 2 · version 1 (the sins)")
        self.assertEqual([tool["name"] for tool in catalog["tools"]], ["music_visualizer.py"])
        self.assertEqual(set(RAP_PAGES), {"Seven-Deadly-Sins", "Homewood-and-Trafalgar", "Made-in-Abyss", "Vagabond", "NanoFtheAbove", "Future-Projects"})
        lede, markup = rap_content("Vagabond", catalog, "../../../")
        self.assertIn("1 song from music_work (Vagabond)", lede)
        self.assertEqual(BeautifulSoup(markup, "html.parser").h2.get_text(), "1 song")
        self.assertIn("&lt;b&gt;Line two&lt;/b&gt;", markup)
        self.assertIn("Not on GitHub yet", markup)
        _, future = rap_content("Future-Projects", catalog, "../../../")
        soup = BeautifulSoup(future, "html.parser")
        self.assertIn("print(&#x27;viz&#x27;)", future)
        self.assertEqual([h.get_text() for h in soup.select("h3.catalog-group")], ["New Folder"])
        self.assertIsNotNone(soup.find(id="catalog-tools-title"))
        self.assertEqual(rap_content("Made-in-Abyss", catalog, ""), ("No music_work folder is placed on this page yet.", ""))


if __name__ == "__main__":
    unittest.main()
