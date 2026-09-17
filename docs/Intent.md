# Project Name

OCRAgent

## Problem Statement

Business need to understand both the data in a document and the structure of the document for two reasons: the data has value only when the extracted results are accurate and the organization of the data provides context that contributes to understanding the purpose of the document. For example, letters always have a header providing reference context, a closing section identifying the individual sender and the rest of the content explains the reason for the letter. A letter saying "pay now" is important if it's from a Customer Service Representative but urgent if it is from a Collections Agent. Extracting data from documents is non-trivial; it involves identifying the characters, then clustering them into words or numbers and combining those further to create paragraphs, tables and other higher level constructs. Identifying the individual characters requires intelligence and it doesn't always work. Once the individual characters and data elements are identified, the context provided by positioning can be important; a set of blocks of content are a "table row" because they are all bounded by the same horizontal "top" and "bottom" coordinates. While other products report some raw confidence information, they don't report a "this can't be trusted" judgement and this application needs to provide that in a clear statement. 

## Primary users

This application will be a tool that can be integrated into other applications. It is not intended to be used directly by people but what it produces will be used by people. This means that the "trust threshold" must be selecteable. If the consuming application is only trying to understand the structure of the document, it doesn't care what the data values are. At the other extreme, if this capability is extacting data from a medical history, even a single missing data item is important and must be investigated. The requirement then is that this capability must understand the difference between recognizing structure, recognizing data capture and measuring that against threshholds provided by the consuming application.

## "-Ilities"

Non

## Security

Because this product provides a capabilty on which other services are built, it assumes the issues of authentication and authorization will be handled by the consumning application or service. However, this product must not leak extracted information outside this scope. A prototype of this product was built using PaddleOCR and a model hosted by Ollama; both of these capabilities have the ability to connect to the Internet and, if they are used it ust be verified that they will not exfiltrate extracted information to other services (especially for model training). This applies to any capability used to implement this product.

## Core Capabilities

This application accepts a PDF and extracts structure, data and extraction confidence information from it. The term "structure" means the location of each recognized data item and the relationship of this item to the other data items near it. Additional information about "structure" will be provided in the detailed design. When extraction confidence thresholds are met, data is returned in a structured form. If a form is not provided, this application will use location clustering information to infer a record structure. Data within recognized tables will be organized by row, content presented in bullet lists and numbered lists will be collected into arrays, consecutive lines of text will be collected into "paragraphs" 

## Out of Scope

A version 2 feature will be to allow a record structure to be provided and the data from this tool will be returned in that form. 
Constraints: blocks of lines will be a presented as a "paragraph" regardless of the overall context as it's not possible for this application to be certain of the context of the text block (a group of lines of text at the top of a document might be an address or they might be reference data). 


## Success Criteria

This tool must know what it does not know; the extraction confidence scores need to support this and the tool must report the confidence scores. Data must be grouped by page and related structure. 
