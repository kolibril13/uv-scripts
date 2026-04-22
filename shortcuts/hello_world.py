#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pywebview>=5.3",
# ]
# ///

"""Open a small native window that says hello world."""

import webview

HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>hello</title>
    <style>
      html, body {
        margin: 0;
        height: 100%;
        font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      h1 {
        margin: 0;
        font-size: 48px;
        font-weight: 600;
        letter-spacing: -0.02em;
      }
      .dot {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #22d3ee;
        margin-right: 14px;
        vertical-align: middle;
        box-shadow: 0 0 24px #22d3ee;
      }
    </style>
  </head>
  <body>
    <h1><span class="dot"></span>hello world</h1>
  </body>
</html>
"""


def main() -> None:
    window = webview.create_window(
        title="hello",
        html=HTML,
        width=420,
        height=220,
        resizable=False,
        on_top=True,
    )
    webview.start(gui="cocoa")
    _ = window


if __name__ == "__main__":
    main()
