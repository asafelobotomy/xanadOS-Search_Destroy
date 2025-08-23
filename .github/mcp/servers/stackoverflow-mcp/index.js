#!/usr/bin/env node

/**
 * StackOverflow MCP Server
 * Provides access to StackOverflow questions, answers, and developer knowledge
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ErrorCode,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  McpError,
  ReadResourceRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

class StackOverflowMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'stackoverflow-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          resources: {},
          tools: {},
          notifications: {},
        },
      }
    );
    
    this.apiKey = process.env.STACKOVERFLOW_API_KEY;
    this.baseUrl = 'https://api.stackexchange.com/2.3';
    this.site = process.env.STACKOVERFLOW_SITE || 'stackoverflow';
    this.cache = new Map();
    this.cacheTimeout = 10 * 60 * 1000; // 10 minutes
    this.rateLimitDelay = 100; // 100ms between requests to respect rate limits
    
    this.setupHandlers();
  }

  setupHandlers() {
    // List available StackOverflow resources
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      try {
        const resources = [
          {
            uri: 'stackoverflow://trending/questions',
            mimeType: 'application/json',
            name: 'Trending Questions',
            description: 'Currently trending questions on StackOverflow',
          },
          {
            uri: 'stackoverflow://featured/questions',
            mimeType: 'application/json',
            name: 'Featured Questions',
            description: 'Featured bounty questions on StackOverflow',
          },
          {
            uri: 'stackoverflow://hot/questions',
            mimeType: 'application/json',
            name: 'Hot Questions',
            description: 'Hot network questions across all Stack Exchange sites',
          },
          {
            uri: 'stackoverflow://tags/popular',
            mimeType: 'application/json',
            name: 'Popular Tags',
            description: 'Most popular tags on StackOverflow',
          },
          {
            uri: 'stackoverflow://users/top',
            mimeType: 'application/json',
            name: 'Top Users',
            description: 'Top users by reputation on StackOverflow',
          },
        ];
        
        return { resources };
      } catch (error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to list StackOverflow resources: ${error.message}`
        );
      }
    });

    // Read StackOverflow data
    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const { uri } = request.params;
      
      try {
        const match = uri.match(/^stackoverflow:\/\/(.+?)\/(.+)$/);
        if (!match) {
          throw new McpError(
            ErrorCode.InvalidRequest,
            `Invalid StackOverflow URI: ${uri}`
          );
        }
        
        const [, category, type] = match;
        let content = {};
        
        switch (category) {
          case 'trending':
            content = await this.getTrendingQuestions();
            break;
          case 'featured':
            content = await this.getFeaturedQuestions();
            break;
          case 'hot':
            content = await this.getHotQuestions();
            break;
          case 'tags':
            content = await this.getPopularTags();
            break;
          case 'users':
            content = await this.getTopUsers();
            break;
          default:
            throw new McpError(
              ErrorCode.InvalidRequest,
              `Unknown StackOverflow category: ${category}`
            );
        }
        
        return {
          contents: [
            {
              uri,
              mimeType: 'application/json',
              text: JSON.stringify(content, null, 2),
            },
          ],
        };
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Failed to read StackOverflow data: ${error.message}`
        );
      }
    });

    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'search_questions',
            description: 'Search for questions on StackOverflow',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query for questions',
                },
                tags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Tags to filter by (e.g., ["javascript", "react"])',
                },
                sort: {
                  type: 'string',
                  enum: ['relevance', 'activity', 'votes', 'creation'],
                  description: 'Sort order for results',
                  default: 'relevance',
                },
                limit: {
                  type: 'number',
                  description: 'Number of results to return',
                  default: 10,
                  minimum: 1,
                  maximum: 100,
                },
                accepted_only: {
                  type: 'boolean',
                  description: 'Only return questions with accepted answers',
                  default: false,
                },
              },
              required: ['query'],
            },
          },
          {
            name: 'get_question_details',
            description: 'Get detailed information about a specific question',
            inputSchema: {
              type: 'object',
              properties: {
                question_id: {
                  type: 'number',
                  description: 'StackOverflow question ID',
                },
                include_answers: {
                  type: 'boolean',
                  description: 'Include answers in the response',
                  default: true,
                },
                include_comments: {
                  type: 'boolean',
                  description: 'Include comments in the response',
                  default: false,
                },
              },
              required: ['question_id'],
            },
          },
          {
            name: 'search_answers',
            description: 'Search for answers on StackOverflow',
            inputSchema: {
              type: 'object',
              properties: {
                query: {
                  type: 'string',
                  description: 'Search query for answers',
                },
                tags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Tags to filter by',
                },
                min_score: {
                  type: 'number',
                  description: 'Minimum answer score',
                  default: 0,
                },
                accepted_only: {
                  type: 'boolean',
                  description: 'Only return accepted answers',
                  default: false,
                },
                limit: {
                  type: 'number',
                  description: 'Number of results to return',
                  default: 10,
                  minimum: 1,
                  maximum: 100,
                },
              },
              required: ['query'],
            },
          },
          {
            name: 'get_tag_info',
            description: 'Get information about a specific tag',
            inputSchema: {
              type: 'object',
              properties: {
                tag_name: {
                  type: 'string',
                  description: 'Tag name to get information about',
                },
                include_synonyms: {
                  type: 'boolean',
                  description: 'Include tag synonyms',
                  default: false,
                },
              },
              required: ['tag_name'],
            },
          },
          {
            name: 'get_user_profile',
            description: 'Get user profile information',
            inputSchema: {
              type: 'object',
              properties: {
                user_id: {
                  type: 'number',
                  description: 'StackOverflow user ID',
                },
                include_activity: {
                  type: 'boolean',
                  description: 'Include recent user activity',
                  default: false,
                },
              },
              required: ['user_id'],
            },
          },
          {
            name: 'find_duplicate_questions',
            description: 'Find potential duplicate questions for a given question',
            inputSchema: {
              type: 'object',
              properties: {
                question_title: {
                  type: 'string',
                  description: 'Question title to find duplicates for',
                },
                tags: {
                  type: 'array',
                  items: { type: 'string' },
                  description: 'Tags to narrow down the search',
                },
                limit: {
                  type: 'number',
                  description: 'Number of potential duplicates to return',
                  default: 5,
                  minimum: 1,
                  maximum: 20,
                },
              },
              required: ['question_title'],
            },
          },
        ],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;
      
      try {
        switch (name) {
          case 'search_questions':
            return await this.searchQuestions(args);
          case 'get_question_details':
            return await this.getQuestionDetails(args);
          case 'search_answers':
            return await this.searchAnswers(args);
          case 'get_tag_info':
            return await this.getTagInfo(args);
          case 'get_user_profile':
            return await this.getUserProfile(args);
          case 'find_duplicate_questions':
            return await this.findDuplicateQuestions(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        if (error instanceof McpError) {
          throw error;
        }
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  async makeApiRequest(endpoint, params = {}) {
    const cacheKey = `${endpoint}:${JSON.stringify(params)}`;
    const cached = this.getCachedData(cacheKey);
    if (cached) return cached;
    
    // Add rate limiting delay
    await this.delay(this.rateLimitDelay);
    
    const url = new URL(`${this.baseUrl}${endpoint}`);
    const searchParams = new URLSearchParams({
      site: this.site,
      ...params,
    });
    
    if (this.apiKey) {
      searchParams.append('key', this.apiKey);
    }
    
    url.search = searchParams.toString();
    
    try {
      const response = await fetch(url.toString(), {
        headers: {
          'User-Agent': 'stackoverflow-mcp/1.0.0',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.error_id) {
        throw new Error(`StackOverflow API Error: ${data.error_message}`);
      }
      
      this.setCachedData(cacheKey, data);
      return data;
    } catch (error) {
      throw new Error(`API request failed: ${error.message}`);
    }
  }

  async getTrendingQuestions() {
    try {
      const data = await this.makeApiRequest('/questions', {
        order: 'desc',
        sort: 'hot',
        pagesize: 20,
        filter: 'withbody',
      });
      
      return {
        title: 'Trending Questions',
        total: data.total || 0,
        questions: data.items.map(this.formatQuestion),
        generated_at: new Date().toISOString(),
      };
    } catch (error) {
      throw new Error(`Failed to get trending questions: ${error.message}`);
    }
  }

  async getFeaturedQuestions() {
    try {
      const data = await this.makeApiRequest('/questions/featured', {
        order: 'desc',
        sort: 'bounty_closes_date',
        pagesize: 20,
        filter: 'withbody',
      });
      
      return {
        title: 'Featured Questions',
        total: data.total || 0,
        questions: data.items.map(this.formatQuestion),
        generated_at: new Date().toISOString(),
      };
    } catch (error) {
      throw new Error(`Failed to get featured questions: ${error.message}`);
    }
  }

  async getHotQuestions() {
    try {
      const data = await this.makeApiRequest('/questions', {
        order: 'desc',
        sort: 'hot',
        pagesize: 20,
        filter: 'withbody',
      });
      
      return {
        title: 'Hot Questions',
        total: data.total || 0,
        questions: data.items.map(this.formatQuestion),
        generated_at: new Date().toISOString(),
      };
    } catch (error) {
      throw new Error(`Failed to get hot questions: ${error.message}`);
    }
  }

  async getPopularTags() {
    try {
      const data = await this.makeApiRequest('/tags', {
        order: 'desc',
        sort: 'popular',
        pagesize: 50,
      });
      
      return {
        title: 'Popular Tags',
        total: data.total || 0,
        tags: data.items.map(tag => ({
          name: tag.name,
          count: tag.count,
          has_synonyms: tag.has_synonyms,
          is_moderator_only: tag.is_moderator_only,
          is_required: tag.is_required,
          description: tag.excerpt_last_body,
        })),
        generated_at: new Date().toISOString(),
      };
    } catch (error) {
      throw new Error(`Failed to get popular tags: ${error.message}`);
    }
  }

  async getTopUsers() {
    try {
      const data = await this.makeApiRequest('/users', {
        order: 'desc',
        sort: 'reputation',
        pagesize: 20,
      });
      
      return {
        title: 'Top Users',
        total: data.total || 0,
        users: data.items.map(user => ({
          user_id: user.user_id,
          display_name: user.display_name,
          reputation: user.reputation,
          user_type: user.user_type,
          profile_image: user.profile_image,
          link: user.link,
          location: user.location,
          creation_date: new Date(user.creation_date * 1000).toISOString(),
          last_access_date: new Date(user.last_access_date * 1000).toISOString(),
          badge_counts: user.badge_counts,
        })),
        generated_at: new Date().toISOString(),
      };
    } catch (error) {
      throw new Error(`Failed to get top users: ${error.message}`);
    }
  }

  async searchQuestions(args) {
    const { query, tags = [], sort = 'relevance', limit = 10, accepted_only = false } = args;
    
    try {
      const params = {
        order: 'desc',
        sort: sort,
        pagesize: Math.min(limit, 100),
        q: query,
        filter: 'withbody',
      };
      
      if (tags.length > 0) {
        params.tagged = tags.join(';');
      }
      
      if (accepted_only) {
        params.accepted = 'True';
      }
      
      const data = await this.makeApiRequest('/search', params);
      
      const results = {
        query,
        tags,
        sort,
        total_results: data.total || 0,
        questions: data.items.map(this.formatQuestion),
        has_more: data.has_more,
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Question search failed: ${error.message}`);
    }
  }

  async getQuestionDetails(args) {
    const { question_id, include_answers = true, include_comments = false } = args;
    
    try {
      let filter = 'withbody';
      if (include_answers) {
        filter = '!9YdnSM68S';  // Includes answers
      }
      if (include_comments) {
        filter = '!9YdnSMC)M';  // Includes answers and comments
      }
      
      const data = await this.makeApiRequest(`/questions/${question_id}`, {
        filter: filter,
      });
      
      if (!data.items || data.items.length === 0) {
        throw new Error(`Question ${question_id} not found`);
      }
      
      const question = data.items[0];
      const details = {
        question: this.formatQuestion(question),
        answers: question.answers ? question.answers.map(this.formatAnswer) : [],
        comments: question.comments ? question.comments.map(this.formatComment) : [],
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(details, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get question details: ${error.message}`);
    }
  }

  async searchAnswers(args) {
    const { query, tags = [], min_score = 0, accepted_only = false, limit = 10 } = args;
    
    try {
      const params = {
        order: 'desc',
        sort: 'votes',
        pagesize: Math.min(limit, 100),
        q: query,
        filter: 'withbody',
      };
      
      if (tags.length > 0) {
        params.tagged = tags.join(';');
      }
      
      if (min_score > 0) {
        params.min = min_score;
      }
      
      if (accepted_only) {
        params.accepted = 'True';
      }
      
      const data = await this.makeApiRequest('/search', params);
      
      // Filter for questions with good answers
      const questionsWithAnswers = data.items.filter(q => q.answer_count > 0);
      
      const results = {
        query,
        tags,
        min_score,
        total_results: questionsWithAnswers.length,
        questions_with_answers: questionsWithAnswers.map(this.formatQuestion),
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Answer search failed: ${error.message}`);
    }
  }

  async getTagInfo(args) {
    const { tag_name, include_synonyms = false } = args;
    
    try {
      const data = await this.makeApiRequest(`/tags/${tag_name}/info`);
      
      if (!data.items || data.items.length === 0) {
        throw new Error(`Tag '${tag_name}' not found`);
      }
      
      const tag = data.items[0];
      const tagInfo = {
        name: tag.name,
        count: tag.count,
        has_synonyms: tag.has_synonyms,
        is_moderator_only: tag.is_moderator_only,
        is_required: tag.is_required,
        description: tag.excerpt_last_body,
        wiki_last_body: tag.wiki_last_body,
      };
      
      if (include_synonyms && tag.has_synonyms) {
        const synonymsData = await this.makeApiRequest(`/tags/${tag_name}/synonyms`);
        tagInfo.synonyms = synonymsData.items || [];
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(tagInfo, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get tag info: ${error.message}`);
    }
  }

  async getUserProfile(args) {
    const { user_id, include_activity = false } = args;
    
    try {
      const data = await this.makeApiRequest(`/users/${user_id}`);
      
      if (!data.items || data.items.length === 0) {
        throw new Error(`User ${user_id} not found`);
      }
      
      const user = data.items[0];
      const profile = {
        user_id: user.user_id,
        display_name: user.display_name,
        reputation: user.reputation,
        user_type: user.user_type,
        profile_image: user.profile_image,
        link: user.link,
        location: user.location,
        about_me: user.about_me,
        website_url: user.website_url,
        creation_date: new Date(user.creation_date * 1000).toISOString(),
        last_access_date: new Date(user.last_access_date * 1000).toISOString(),
        badge_counts: user.badge_counts,
        question_count: user.question_count,
        answer_count: user.answer_count,
        up_vote_count: user.up_vote_count,
        down_vote_count: user.down_vote_count,
      };
      
      if (include_activity) {
        const activityData = await this.makeApiRequest(`/users/${user_id}/timeline`, {
          pagesize: 20,
        });
        profile.recent_activity = activityData.items || [];
      }
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(profile, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Failed to get user profile: ${error.message}`);
    }
  }

  async findDuplicateQuestions(args) {
    const { question_title, tags = [], limit = 5 } = args;
    
    try {
      const params = {
        order: 'desc',
        sort: 'relevance',
        pagesize: limit * 2, // Get more to filter better
        q: question_title,
        filter: 'withbody',
      };
      
      if (tags.length > 0) {
        params.tagged = tags.join(';');
      }
      
      const data = await this.makeApiRequest('/search', params);
      
      // Score potential duplicates based on title similarity and tags
      const potentialDuplicates = data.items
        .map(q => ({
          ...this.formatQuestion(q),
          similarity_score: this.calculateSimilarity(question_title, q.title),
        }))
        .sort((a, b) => b.similarity_score - a.similarity_score)
        .slice(0, limit);
      
      const results = {
        original_title: question_title,
        tags,
        potential_duplicates: potentialDuplicates,
        search_results_count: data.total || 0,
      };
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(results, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`Duplicate search failed: ${error.message}`);
    }
  }

  formatQuestion(question) {
    return {
      question_id: question.question_id,
      title: question.title,
      body: question.body,
      score: question.score,
      view_count: question.view_count,
      answer_count: question.answer_count,
      comment_count: question.comment_count,
      tags: question.tags,
      is_answered: question.is_answered,
      accepted_answer_id: question.accepted_answer_id,
      creation_date: new Date(question.creation_date * 1000).toISOString(),
      last_activity_date: new Date(question.last_activity_date * 1000).toISOString(),
      owner: question.owner ? {
        user_id: question.owner.user_id,
        display_name: question.owner.display_name,
        reputation: question.owner.reputation,
        profile_image: question.owner.profile_image,
      } : null,
      link: question.link,
      bounty_amount: question.bounty_amount,
      bounty_closes_date: question.bounty_closes_date ? 
        new Date(question.bounty_closes_date * 1000).toISOString() : null,
    };
  }

  formatAnswer(answer) {
    return {
      answer_id: answer.answer_id,
      question_id: answer.question_id,
      body: answer.body,
      score: answer.score,
      is_accepted: answer.is_accepted,
      comment_count: answer.comment_count,
      creation_date: new Date(answer.creation_date * 1000).toISOString(),
      last_activity_date: new Date(answer.last_activity_date * 1000).toISOString(),
      owner: answer.owner ? {
        user_id: answer.owner.user_id,
        display_name: answer.owner.display_name,
        reputation: answer.owner.reputation,
        profile_image: answer.owner.profile_image,
      } : null,
      link: answer.link,
    };
  }

  formatComment(comment) {
    return {
      comment_id: comment.comment_id,
      post_id: comment.post_id,
      body: comment.body,
      score: comment.score,
      creation_date: new Date(comment.creation_date * 1000).toISOString(),
      owner: comment.owner ? {
        user_id: comment.owner.user_id,
        display_name: comment.owner.display_name,
        reputation: comment.owner.reputation,
      } : null,
    };
  }

  calculateSimilarity(str1, str2) {
    const words1 = str1.toLowerCase().split(/\s+/);
    const words2 = str2.toLowerCase().split(/\s+/);
    const intersection = words1.filter(word => words2.includes(word));
    const union = [...new Set([...words1, ...words2])];
    return intersection.length / union.length;
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  getCachedData(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  setCachedData(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('StackOverflow MCP server running on stdio');
  }
}

const server = new StackOverflowMCPServer();
server.run().catch(console.error);
