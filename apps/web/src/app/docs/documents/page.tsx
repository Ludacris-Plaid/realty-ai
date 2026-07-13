"use client";

import { FileText, Upload, Search, Database, FileSearch, FileCheck, Scale, Home, Wrench, FileSignature, Layers } from "lucide-react";

const docCategories = [
  { name: "Contracts", icon: FileSignature, count: "Purchase agreements, counter-offers, addenda", color: "bg-blue-50 text-blue-600" },
  { name: "Disclosures", icon: FileCheck, count: "Seller disclosures, lead-based paint, property condition", color: "bg-rose-50 text-rose-600" },
  { name: "Inspections", icon: Wrench, count: "Home inspection, termite, roof, HVAC reports", color: "bg-amber-50 text-amber-600" },
  { name: "Appraisals", icon: Scale, count: "Appraisal reports, valuation analyses, reconsideration letters", color: "bg-purple-50 text-purple-600" },
  { name: "Title Documents", icon: FileSearch, count: "Title commitments, policies, lien searches", color: "bg-emerald-50 text-emerald-600" },
  { name: "Closing Documents", icon: Home, count: "Closing disclosures, settlement statements, deeds", color: "bg-cyan-50 text-cyan-600" },
];

export default function DocumentsDocs() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Documents & Contracts</h1>
        <p className="mt-2 text-lg text-gray-500">
          Upload, organize, and analyze real estate documents with AI-powered text extraction and natural language querying.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Upload className="h-5 w-5 text-brand-500" />
          Upload & Management
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Documents can be uploaded via drag-and-drop, file picker, or forwarded directly from your email. Supported formats include PDF, DOCX, PNG, and JPEG. Each document is automatically assigned to a category based on content analysis and OCR header detection.
          </p>
          <p className="text-sm text-gray-600 leading-relaxed">
            Uploaded files are encrypted at rest and stored in S3-compatible object storage. Access control follows your brokerage&rsquo;s team hierarchy — admins see all documents, agents see documents linked to their own leads and listings.
          </p>
          <div className="rounded-lg bg-gray-50 border border-gray-100 p-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">Upload Metadata</h4>
            <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
              <li>Original filename with version tracking</li>
              <li>Upload timestamp and uploading user</li>
              <li>Linked lead, listing, or transaction ID</li>
              <li>Auto-detected category and confidence score</li>
              <li>Page count, file size, and checksum</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <FileSearch className="h-5 w-5 text-brand-500" />
          AI Text Extraction
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            When a PDF is uploaded, the DocAnalyzer agent immediately processes it through a multi-stage extraction pipeline:
          </p>
          <ol className="text-sm text-gray-600 space-y-1.5 list-decimal list-inside">
            <li><strong>OCR pass</strong> — Tesseract-based OCR extracts text from scanned documents and images.</li>
            <li><strong>Structure parsing</strong> — Headers, paragraphs, tables, signatures, and form fields are identified.</li>
            <li><strong>Entity extraction</strong> — Dates, dollar amounts, party names, addresses, and clauses are tagged.</li>
            <li><strong>Category assignment</strong> — The document is classified into a category with a confidence score.</li>
            <li><strong>Embedding generation</strong> — Text chunks are vectorized and stored in the knowledge base for retrieval.</li>
          </ol>
          <p className="text-sm text-gray-500">
            Extraction results are visible in the document preview panel alongside the original PDF. You can correct any misidentified fields and the feedback improves future extractions.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Layers className="h-5 w-5 text-brand-500" />
          Document Categories
        </h2>
        <p className="text-sm text-gray-600 leading-relaxed">Documents are organized into six categories. Category assignment is automatic but can be overridden manually.</p>
        <div className="grid gap-3 sm:grid-cols-2">
          {docCategories.map((c) => (
            <div key={c.name} className="rounded-xl border border-gray-200 bg-white p-5">
              <div className="flex items-center gap-3 mb-2">
                <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${c.color}`}>
                  <c.icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold text-gray-800">{c.name}</h3>
              </div>
              <p className="text-xs text-gray-500">{c.count}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Search className="h-5 w-5 text-brand-500" />
          Asking Questions About Documents
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Once documents are processed, you can ask natural-language questions and get answers grounded in the document content. Example questions:
          </p>
          <div className="rounded-lg bg-gray-50 border border-gray-100 p-4 space-y-1.5 text-sm text-gray-600">
            <p>&ldquo;What is the earnest money amount in the purchase agreement for 123 Oak St?&rdquo;</p>
            <p>&ldquo;When is the inspection contingency deadline?&rdquo;</p>
            <p>&ldquo;Does the disclosure mention any water damage in the basement?&rdquo;</p>
            <p>&ldquo;Summarize all financial terms in this contract.&rdquo;</p>
          </div>
          <p className="text-sm text-gray-500">
            Answers include inline citations showing the source page and paragraph. If the question can&rsquo;t be answered from the available documents, the agent responds with what&rsquo;s known and what&rsquo;s missing.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="flex items-center gap-2 text-xl font-semibold text-gray-900">
          <Database className="h-5 w-5 text-brand-500" />
          RAG Pipeline
        </h2>
        <div className="rounded-xl border border-gray-200 bg-white p-6 space-y-3">
          <p className="text-sm text-gray-600 leading-relaxed">
            Document Q&amp;A is powered by a Retrieval-Augmented Generation pipeline. When you ask a question, it doesn&rsquo;t send the full document to the LLM — it retrieves only the relevant chunks.
          </p>
          <div className="rounded-lg bg-brand-50 border border-brand-100 p-4">
            <h4 className="text-sm font-semibold text-brand-700 mb-2">Query Flow</h4>
            <ol className="text-sm text-brand-700 space-y-1 list-decimal list-inside">
              <li>Your question is embedded into a vector using <span className="font-mono text-xs bg-brand-100 px-1 rounded">text-embedding-3-small</span></li>
              <li>The vector is searched against the document chunk store (pgvector with cosine similarity, top-10 results)</li>
              <li>Retrieved chunks are combined with the question as context for the LLM prompt</li>
              <li>The LLM generates an answer citing the source chunks by document name, page number, and paragraph</li>
              <li>Chunks below the 0.65 similarity threshold are discarded — the model says what it doesn&rsquo;t know</li>
            </ol>
          </div>
          <p className="text-sm text-gray-500">
            The vector store is per-user scoped by default, with optional brokerage-wide shared indexes for templates and standard forms. Documents can be re-indexed on demand if you upload a revised version.
          </p>
        </div>
      </section>
    </div>
  );
}
