export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          user_id: string
          email: string
          oauth_provider: string
          oauth_id: string
          credits: number
          created_at: string | null
          is_active: boolean | null
          first_name: string | null
          last_name: string | null
        }
        Insert: {
          user_id?: string
          email: string
          oauth_provider: string
          oauth_id: string
          credits?: number
          created_at?: string | null
          is_active?: boolean | null
          first_name?: string | null
          last_name?: string | null
        }
        Update: {
          user_id?: string
          email?: string
          oauth_provider?: string
          oauth_id?: string
          credits?: number
          created_at?: string | null
          is_active?: boolean | null
          first_name?: string | null
          last_name?: string | null
        }
      }
      job_bookmarks: {
        Row: {
          bookmark_id: string
          user_id: string
          title: string
          company: string
          location: string | null
          source: string
          source_url: string | null
          description: string | null
          application_status: Database["public"]["Enums"]["application_status_enum"] | null
          created_at: string | null
          job_industry_id: number | null
        }
        Insert: {
          bookmark_id?: string
          user_id: string
          title: string
          company: string
          location?: string | null
          source: string
          source_url?: string | null
          description?: string | null
          application_status?: Database["public"]["Enums"]["application_status_enum"] | null
          created_at?: string | null
          job_industry_id?: number | null
        }
        Update: {
          bookmark_id?: string
          user_id?: string
          title?: string
          company?: string
          location?: string | null
          source?: string
          source_url?: string | null
          description?: string | null
          application_status?: Database["public"]["Enums"]["application_status_enum"] | null
          created_at?: string | null
          job_industry_id?: number | null
        }
      }
      resumes: {
        Row: {
          id: string
          filename: string
          size: number
          uploaded_at: string | null
          object_id: string
          user_id: string
          resume_name: string | null
          experience: Database["public"]["Enums"]["experience_level_enum"] | null
          targeted_job_bookmark_id: string | null
          match_score: number | null
          recommended_tips: string | null
        }
        Insert: {
          id?: string
          filename: string
          size: number
          uploaded_at?: string | null
          object_id: string
          user_id: string
          resume_name?: string | null
          experience?: Database["public"]["Enums"]["experience_level_enum"] | null
          targeted_job_bookmark_id?: string | null
          match_score?: number | null
          recommended_tips?: string | null
        }
        Update: {
          id?: string
          filename?: string
          size?: number
          uploaded_at?: string | null
          object_id?: string
          user_id?: string
          resume_name?: string | null
          experience?: Database["public"]["Enums"]["experience_level_enum"] | null
          targeted_job_bookmark_id?: string | null
          match_score?: number | null
          recommended_tips?: string | null
        }
      }
      job_analyses: {
        Row: {
          analysis_id: string
          user_id: string
          job_bookmark_id: string | null
          confidence_score: number | null
          is_authentic: boolean | null
          evidence: string | null
          analysis_type: string
          credits_used: number | null
          created_at: string | null
        }
        Insert: {
          analysis_id?: string
          user_id: string
          job_bookmark_id?: string | null
          confidence_score?: number | null
          is_authentic?: boolean | null
          evidence?: string | null
          analysis_type: string
          credits_used?: number | null
          created_at?: string | null
        }
        Update: {
          analysis_id?: string
          user_id?: string
          job_bookmark_id?: string | null
          confidence_score?: number | null
          is_authentic?: boolean | null
          evidence?: string | null
          analysis_type?: string
          credits_used?: number | null
          created_at?: string | null
        }
      }
      job_documents: {
        Row: {
          id: number
          user_id: string
          filename: string
          file_size: number
          mime_type: string
          object_id: string
          extracted_text: string | null
          processing_status: string | null
          analysis_result: Json | null
          created_at: string | null
          processed_at: string | null
        }
        Insert: {
          id?: number
          user_id: string
          filename: string
          file_size: number
          mime_type: string
          object_id: string
          extracted_text?: string | null
          processing_status?: string | null
          analysis_result?: Json | null
          created_at?: string | null
          processed_at?: string | null
        }
        Update: {
          id?: number
          user_id?: string
          filename?: string
          file_size?: number
          mime_type?: string
          object_id?: string
          extracted_text?: string | null
          processing_status?: string | null
          analysis_result?: Json | null
          created_at?: string | null
          processed_at?: string | null
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      application_status_enum: "interested" | "applied" | "interviewing" | "interviewed_passed" | "interviewed_failed"
      experience_level_enum: "junior" | "mid_senior" | "director" | "executive"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

